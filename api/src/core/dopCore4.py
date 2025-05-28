from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling, profile_time
import models
from copy import deepcopy




@profile_time
def calculate_plan_min_retooling(spec: models.ProductionSpecification):
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    orders = spec.orders
    original_ready_plates = [deepcopy(plate) for plate in spec.ready_plates]  # Сохраняем копию исходных готовых плит
    ready_plates = [deepcopy(plate) for plate in spec.ready_plates]  # Копия для модификации

    # Получаем плиты, которые нужно изготовить, и обновленные готовые плиты
    need_create_plates, updated_ready_plates = hasReadyPlate(orders, ready_plates)

    # Вычисляем использованные готовые плиты
    used_ready_plates = []
    for original in original_ready_plates:
        updated = next(
            (p for p in updated_ready_plates
             if (p.length == original.length and
                 p.width == original.width and
                 p.height == original.height and
                 p.concrete_class == original.concrete_class and
                 p.wire_bottom == original.wire_bottom and
                 p.wire_top == original.wire_top)),
            None
        )
        if updated:
            used_count = original.count - updated.count
            if used_count > 0:
                used_plate = deepcopy(original)
                used_plate.count = used_count
                used_ready_plates.append(used_plate)
        else:
            # Все плиты этого типа использованы
            used_plate = deepcopy(original)
            used_plate.count = original.count
            used_ready_plates.append(used_plate)

    is_real = reality_check(need_create_plates, available_tracks, track_len)
    tracks_config = bestPlatesMinRetooling(available_tracks, track_len, need_create_plates, spec.directory)

    # Собираем неуместившиеся плиты
    unplaced_plates = []
    for date_entry in need_create_plates:
        date = date_entry["date"]
        for plate in date_entry["plate"]:
            if plate.count > 0:
                unplaced_plates.append({
                    "date": date,
                    "plate": [deepcopy(plate)]  # Оборачиваем в список для merge_plates
                })
    unplaced_plates_merged = merge_plates(unplaced_plates)

    retooling_cost = count_of_retooling(tracks_config, spec.directory.retooling.price)

    return (
        tracks_config,           # Конечные параметры переналадчика
        used_ready_plates,       # Использованные готовые плиты
        unplaced_plates_merged,  # Плиты, не уместившиеся на дорожках
        updated_ready_plates,    # Оставшиеся готовые плиты
        retooling_cost,
        is_real
    )

@profile_time
def bestPlatesMinRetooling(trackDays, track_len: int, needPlates, prices):
    """
    Для минимизации переналадок пытаемся для каждой дорожки использовать тот же тип плит,
    что и в предыдущей дорожке (одинаковые: ширина, высота, concrete_class, wire_bottom, wire_top).
    Если выбранная ранее группа недоступна или не даёт заполнения, выбираем группу, которая
    обеспечивает максимальное заполнение дорожки. Таким образом, последовательные дорожки будут иметь
    одинаковые параметры, что снижает количество переналадок.
    """
    tracks_config = []

    # Группируем все плиты по их характеристикам
    plate_groups = defaultdict(list)
    for date_entry in needPlates:
        for plate in date_entry["plate"]:
            if plate.count > 0:
                key = (
                    plate.width,
                    plate.height,
                    plate.concrete_class,
                    plate.wire_bottom,
                    plate.wire_top
                )
                plate_groups[key].append(deepcopy(plate))

    # Сортируем группы так, чтобы сначала обрабатывать самые длинные плиты
    sorted_group_keys = sorted(
        plate_groups.keys(),
        key=lambda k: sum(p.length * p.count for p in plate_groups[k]),
        reverse=True
    )

    # Обрабатываем каждую дорожку
    for track_info in trackDays:
        for _ in range(track_info.count):
            current_config = None
            track_remaining = track_len

            # Попробуем выбрать оптимальную группу для этой дорожки
            for group_key in sorted_group_keys:
                plates_in_group = plate_groups[group_key]
                if not plates_in_group:
                    continue

                width, height, concrete_class, wire_bottom, wire_top = group_key

                # Если ещё нет конфигурации — создаём
                if current_config is None:
                    current_config = models.TrackConfig(
                        day=track_info.day,
                        height=height,
                        width=width,
                        free_len=track_len,
                        useful_len=0,
                        concrete_class=concrete_class,
                        wire_bottom=wire_bottom,
                        wire_top=wire_top,
                        total_cost=0,
                        plates=[],
                    )
                    tracks_config.append(current_config)

                # Сортируем плиты в группе по убыванию длины
                plates_sorted = sorted(plates_in_group, key=lambda x: x.length, reverse=True)

                for plate in plates_sorted:
                    if plate.count <= 0 or track_remaining < plate.length:
                        continue

                    max_plates = min(plate.count, track_remaining // plate.length)
                    if max_plates == 0:
                        continue

                    # Добавляем плиты в дорожку
                    current_config.plates.extend([deepcopy(plate)] * max_plates)
                    current_config.free_len -= plate.length * max_plates
                    current_config.useful_len += plate.length * max_plates
                    plate.count -= max_plates
                    track_remaining -= plate.length * max_plates

                    # Удаляем полностью израсходованные плиты
                    if plate.count == 0:
                        plates_in_group.remove(plate)

                # После добавления всех возможных плит из группы — выходим
                break  # чтобы не менять конфигурацию

            # Подсчёт стоимости после заполнения дорожки
            if current_config and current_config.plates:
                concrete_price = next(
                    cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class
                )
                cost = 0
                for plate in current_config.plates:
                    cost += plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000 \
                            * concrete_price
                cost += len(current_config.plates) * prices.wire.price * (
                            current_config.wire_bottom + current_config.wire_top)
                current_config.total_cost = cost

                # Стоимость свободного места
                free_vol = current_config.free_len / 1000 * current_config.height / 1000 * current_config.width / 1000
                current_config.free_cost = free_vol * concrete_price if concrete_price else 0
                current_config.full_cost = current_config.total_cost + current_config.free_cost

            # Уменьшаем количество доступных дорожек
            track_info.count -= 1

    return tracks_config

