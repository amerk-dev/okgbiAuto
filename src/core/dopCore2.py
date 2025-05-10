from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import time
from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling
import models
from copy import deepcopy

def profile_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result
    return wrapper


@profile_time
def calculate_plan_max_fill(spec: models.ProductionSpecification):
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
    tracks_config = bestPlatesMaxFill(available_tracks, track_len, need_create_plates, spec.directory)

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
def bestPlatesMaxFill(trackDays, track_len: int, needPlates, prices):
    """
    Для каждой дорожки ищется такая группа совместимых плит (по ширине, высоте, классу и проводам),
    для которой с помощью алгоритма динамического программирования (задача о рюкзаке) можно максимально заполнить дорожку.
    """
    tracks_config = []

    # Группируем плиты по параметрам (ширина, высота, класс бетона)
    grouped_plates = defaultdict(list)
    for date_entry in needPlates:
        for plate in date_entry["plate"]:
            if plate.count > 0:
                key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                grouped_plates[key].append(deepcopy(plate))

    # Сортируем каждую группу по длине (от большего к меньшему)
    for key in grouped_plates:
        grouped_plates[key].sort(key=lambda p: p.length, reverse=True)

    # Используем дорожки
    for track_info in trackDays:
        for _ in range(track_info.count):
            current_config = None
            available_key = None

            # Перебираем все группы плит
            for key in list(grouped_plates.keys()):
                width, height, concrete_class, wire_bottom, wire_top = key
                plates = grouped_plates[key]

                # Проверяем, можно ли начать новую конфигурацию
                if current_config is None:
                    current_config = models.TrackConfig(
                        day=track_info.day,
                        height=height,
                        width=width,
                        concrete_class=concrete_class,
                        wire_bottom=wire_bottom,
                        wire_top=wire_top,
                        free_len=track_len,
                        useful_len=0,
                        total_cost=0,
                        plates=[],
                        free_cost=0,
                        full_cost=0
                    )
                    tracks_config.append(current_config)
                    available_key = key

                # Если текущая группа не совпадает с конфигурацией — пропускаем
                if key != available_key:
                    continue

                # Укладываем плиты
                concrete_price = next(cc.price for cc in prices.concrete_classes if cc.name == concrete_class)
                for plate in plates:
                    if current_config.free_len <= 0:
                        break

                    max_count = min(plate.count, current_config.free_len // plate.length)
                    if max_count <= 0:
                        continue

                    # Укладываем плиты
                    for _ in range(max_count):
                        current_config.plates.append(deepcopy(plate))

                    # Обновляем параметры дорожки
                    current_config.free_len -= plate.length * max_count
                    current_config.useful_len += plate.length * max_count
                    plate.count -= max_count

                    # Расчёт стоимости
                    cost = 0
                    cost += wire_bottom * prices.wire.price * max_count
                    cost += wire_top * prices.wire.price * max_count
                    cost += (plate.length / 1000 * height / 1000 * width / 1000) * concrete_price * max_count
                    current_config.total_cost += cost

                # Убираем пустые группы
                grouped_plates[key] = [p for p in plates if p.count > 0]
                if not grouped_plates[key]:
                    del grouped_plates[key]

            # Если плиты не нашлись — всё равно создаём конфигурацию (например, для отчёта)
            if current_config is None:
                current_config = models.TrackConfig(
                    day=track_info.day,
                    height=0,
                    width=0,
                    concrete_class="",
                    wire_bottom=0,
                    wire_top=0,
                    free_len=track_len,
                    useful_len=0,
                    total_cost=0,
                    plates=[],
                    free_cost=0,
                    full_cost=0
                )
                tracks_config.append(current_config)

        track_info.count = 0  # Освобождаем дорожки

    return tracks_config