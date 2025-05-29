from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling, profile_time
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
def bestPlatesMinMix(trackDays, track_len: int, needPlates, prices):
    """
    Для каждой дорожки выбирается однородная группа плит (одинаковый класс бетона и проводка),
    которая обеспечивает максимально возможное заполнение дорожки при минимальном использовании более дорогих материалов.
    Если заполнение достигает не менее 80% д  лины дорожки, вариант считается приемлемым.
    """
    tracks_config = []
    sorted_needPlates = sorted(needPlates, key=lambda x: x["date"])

    plates_for_date = []
    for date_entry in sorted_needPlates:
        date = date_entry["date"]
        plates_for_date = [deepcopy(p) for p in date_entry["plate"] if p.count > 0]
        if not plates_for_date:
            continue

    available_tracks = trackDays #[t for t in trackDays if t.day == date]
    for track_info in available_tracks:
        for _ in range(track_info.count):
            track_remaining = track_len
            current_config = None
            concrete_price = 0

            def calc_cost_per_length(p):
                try:
                    concrete_price = next(cc.price for cc in prices.concrete_classes if cc.name == p.concrete_class)
                except StopIteration:
                    concrete_price = float('inf')
                volume_cost = (p.length / 1000) * (p.height / 1000) * (p.width / 1000) * concrete_price
                wire_cost = (p.wire_bottom + p.wire_top) * prices.wire.price
                return (volume_cost + wire_cost) / p.length if p.length else float('inf')

            sorted_plates = sorted(
                [p for p in plates_for_date if p.count > 0],
                key=calc_cost_per_length
            )

            for plate in sorted_plates:
                if track_remaining <= 0:
                    break

                if current_config:
                    if not all(getattr(plate, attr) == getattr(current_config, attr) for attr in
                               ['width', 'height', 'concrete_class', 'wire_bottom', 'wire_top']):
                        continue
                else:
                    wire_top = max(sorted_plates, key=lambda plate: sorted_plates.wire_top).wire_top
                    wire_bottom = max(sorted_plates, key=lambda plate: sorted_plates.wire_bottom).wire_bottom
                    concrete_class = max(sorted_plates, key=lambda plate: sorted_plates.concrete_class).concrete_class
                    current_config = models.TrackConfig(
                        day=track_info.day,
                        height=plate.height,
                        width=plate.width,
                        free_len=track_len,
                        useful_len=0,
                        concrete_class=concrete_class,
                        wire_bottom=wire_bottom,
                        wire_top=wire_top,
                        total_cost=0,
                        plates=[]
                    )
                    tracks_config.append(current_config)
                    try:
                        concrete_price = next(
                            cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class)
                    except StopIteration:
                        concrete_price = 0

                max_plates = min(plate.count, track_remaining // plate.length)
                if max_plates > 0:
                    current_config.plates.extend([deepcopy(plate)] * max_plates)
                    current_config.free_len -= plate.length * max_plates
                    current_config.useful_len += plate.length * max_plates
                    track_remaining -= plate.length * max_plates

                    cost = (plate.wire_bottom + plate.wire_top) * prices.wire.price * max_plates
                    cost += (
                                        plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000) * concrete_price * max_plates
                    current_config.total_cost += cost

                    # Обновление count в plates_for_date
                    for p in plates_for_date:
                        if all(getattr(p, attr) == getattr(plate, attr) for attr in
                               ['length', 'width', 'height', 'concrete_class', 'wire_bottom', 'wire_top']):
                            p.count -= max_plates
                            break

            if current_config:
                try:
                    concrete_price = next(
                        cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class)
                except StopIteration:
                    concrete_price = 0
                current_config.free_cost = (
                                                       current_config.free_len / 1000 * current_config.height / 1000 * current_config.width / 1000) * concrete_price
                current_config.full_cost = current_config.free_cost + current_config.total_cost

        track_info.count = 0

    return tracks_config


