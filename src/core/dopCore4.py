from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling, profile_time, calculate_price
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

    retooling_cost = count_of_retooling(tracks_config, spec.directory.retooling.price, spec.retooler)

    return (
        tracks_config,  # Конечные параметры переналадчика
        used_ready_plates,  # Использованные готовые плиты
        unplaced_plates_merged,  # Плиты, не уместившиеся на дорожках
        updated_ready_plates,  # Оставшиеся готовые плиты
        retooling_cost,
        is_real
    )


@profile_time
def bestPlatesMinRetooling(trackDays, track_len: int, needPlates, prices):
    tracks_config = []

    # Разделяем плиты на две группы: с дедлайном и без
    plates_with_deadline = defaultdict(list)
    plates_without_deadline = defaultdict(list)

    for order in needPlates:
        for plate in order["plate"]:
            if plate.count <= 0:
                continue
            if order['date'] is not None:
                key = (plate.width, plate.height)
                plates_with_deadline[key].append(plate)
            else:
                key = (plate.width, plate.height)
                plates_without_deadline[key].append(plate)

    for key in plates_with_deadline:
        plates_with_deadline[key].sort(key=lambda x: x.length, reverse=True)
    for key in plates_without_deadline:
        plates_without_deadline[key].sort(key=lambda x: x.length, reverse=True)

    # Первый этап, плиты с дедлайнами
    for track_info in trackDays:
        for _ in range(track_info.count):
            current_config = None
            available_key = None

            # Перебираем группы плит
            for key in list(plates_with_deadline.keys()):
                width, height = key
                plates = plates_with_deadline[key]

                # Создаем конфигурацию, если возможно
                if current_config is None and plates:
                    wire_top = max(plates, key=lambda plate: plate.wire_top).wire_top
                    wire_bottom = max(plates, key=lambda plate: plate.wire_bottom).wire_bottom
                    concrete_class = max(plates, key=lambda plate: plate.concrete_class).concrete_class
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

                if key != available_key:
                    continue

                # Укладываем плиты
                for plate in plates:
                    if current_config.free_len <= 0:
                        break

                    max_count = min(plate.count, current_config.free_len // plate.length)
                    if max_count <= 0:
                        continue

                    # Добавляем плиты
                    current_config.plates.extend([deepcopy(plate)] * max_count)
                    current_config.free_len -= plate.length * max_count
                    current_config.useful_len += plate.length * max_count
                    plate.count -= max_count

                # Очищаем пустые группы
                plates_with_deadline[key] = [p for p in plates if p.count > 0]
                if not plates_with_deadline[key]:
                    del plates_with_deadline[key]

            if current_config:
                current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(
                    current_config, prices)

    # Второй этап, плиты без дедлайнов
    for track_info in trackDays:
        for _ in range(track_info.count):
            current_config = None
            available_key = None
            # Перебираем группы плит
            for key in list(plates_without_deadline.keys()):
                width, height = key
                plates = plates_without_deadline[key]
                for track in tracks_config:
                    if (track.width, track.height) == (width, height):
                        for plate in plates:
                            if track.free_len > plate.length:
                                track.free_len -= plate.length
                                track.useful_len += plate.length
                                track.total_cost, track.free_cost, track.full_cost = calculate_price(
                                    track, prices)
                                track.wire_top = max(track.plates, key=lambda plate: plate.wire_top).wire_top
                                track.wire_bottom = max(track.plates, key=lambda plate: plate.wire_bottom).wire_bottom
                                track.concrete_class = max(track.plates, key=lambda plate: plate.concrete_class).concrete_class
                                track.plates.append(plate)
                            else:
                                break

                # Создаем конфигурацию, если возможно
                if current_config is None and plates:
                    wire_top = max(plates, key=lambda plate: plate.wire_top).wire_top
                    wire_bottom = max(plates, key=lambda plate: plate.wire_bottom).wire_bottom
                    concrete_class = max(plates, key=lambda plate: plate.concrete_class).concrete_class
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

                if key != available_key:
                    continue

                # Укладываем плиты
                for plate in plates:
                    if current_config.free_len <= 0:
                        break

                    max_count = min(plate.count, current_config.free_len // plate.length)
                    if max_count <= 0:
                        continue

                    # Добавляем плиты
                    current_config.plates.extend([deepcopy(plate)] * max_count)
                    current_config.free_len -= plate.length * max_count
                    current_config.useful_len += plate.length * max_count
                    plate.count -= max_count

                # Очищаем пустые группы
                plates_without_deadline[key] = [p for p in plates if p.count > 0]
                if not plates_without_deadline[key]:
                    del plates_without_deadline[key]

            if current_config:
                current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(
                    current_config, prices)

        track_info.count = 0  # Освобождаем дорожки

    return tracks_config
