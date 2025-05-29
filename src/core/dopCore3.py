from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling, profile_time, calculate_price
import models
from copy import deepcopy

import time

@profile_time
def calculate_plan_min_mix(spec: models.ProductionSpecification):
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
    tracks_config = bestPlatesMinMix(available_tracks, track_len, need_create_plates, spec.directory)

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
def bestPlatesMinMix(trackDay, track_len: int, needPlates, prices):
    tracks_config = []
    for tracks in trackDay:
        for _ in range(tracks.count):
            track_remaining = track_len
            current_config = None
            available_size = None

            # Разделяем плиты на две группы: с дедлайном и без
            plates_with_deadline = []
            plates_without_deadline = []

            for order in needPlates:
                for plate in order["plate"]:
                    if plate.count <= 0:
                        continue
                    if order['date'] is not None:
                        plates_with_deadline.append(plate)
                    else:
                        plates_without_deadline.append(plate)

            # Сортируем каждую группу по длине (от большего к меньшему)
            plates_with_deadline.sort(key=lambda x: (x.width, x.height, x.wire_top, x.wire_bottom, x.concrete_class), reverse=True)
            plates_without_deadline.sort(key=lambda x: (x.width, x.height, x.wire_top, x.wire_bottom, x.concrete_class), reverse=True)

            # Объединяем группы: сначала плиты с дедлайном, потом без
            sorted_plates = plates_with_deadline + plates_without_deadline

            for plate in sorted_plates:
                if track_remaining <= 0:
                    break

                if current_config:
                    if (plate.width, plate.height) != available_size:
                        continue
                else:
                    wire_top = max(sorted_plates, key=lambda plate: sorted_plates).wire_top
                    wire_bottom = max(sorted_plates, key=lambda plate: sorted_plates).wire_bottom
                    concrete_class = max(sorted_plates, key=lambda plate: sorted_plates).concrete_class
                    current_config = models.TrackConfig(
                        day=tracks.day,
                        height=plate.height,
                        width=plate.width,
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
                    available_size = (plate.width, plate.height)
                    tracks_config.append(current_config)

                max_plates = min(plate.count, track_remaining // plate.length)
                if max_plates > 0:
                    for _ in range(max_plates):
                        current_config.plates.append(deepcopy(plate))
                    current_config.free_len -= plate.length * max_plates
                    current_config.useful_len += plate.length * max_plates
                    plate.count -= max_plates
                    track_remaining -= plate.length * max_plates


                    current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(current_config, prices)



        tracks.count -= 1

    return tracks_config
