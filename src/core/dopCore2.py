from datetime import datetime
from typing import Dict, List
from collections import defaultdict

from loguru import logger

from .core import reality_check, hasReadyPlate, merge_plates, count_of_retooling, profile_time, calculate_price
import models
from copy import deepcopy


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
def bestPlatesMaxFill(trackDays, track_len: int, needPlates, prices):
    """
    Для каждой дорожки ищется группа совместимых плит по ширине и высоте,
    и с помощью алгоритма динамического программирования максимально заполняется.
    """
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

    grouped_plates = defaultdict(list)
    for key in plates_with_deadline:
        grouped_plates[key] = plates_with_deadline[key]
    for key in plates_without_deadline:
        grouped_plates[key].extend(plates_without_deadline[key])

    # Используем дорожки
    for track_info in trackDays:
        for _ in range(track_info.count):
            current_config = None
            available_key = None
            available_size = None

            # Перебираем группы плит
            for key in list(grouped_plates.keys()):
                width, height = key
                plates = grouped_plates[key]

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
                grouped_plates[key] = [p for p in plates if p.count > 0]
                if not grouped_plates[key]:
                    del grouped_plates[key]

            # Создаем пустую конфигурацию, если плит нет
            if current_config:
                current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(
                    current_config, prices)

        track_info.count = 0  # Освобождаем дорожки
    post_calculating(tracks_config, plates_with_deadline)
    return tracks_config


@logger.catch
def post_calculating(track_config, plates_with_deadline):
    for index in range(len(track_config)-1):
        track = track_config[index]
        if track.width != track_config[index + 1].width or track.height != track_config[index + 1].height:
            for plate in track.plates:
                if plate in plates_with_deadline[(plate.width, plate.height)]:
                    break
            else:
                p1 = track.free_cost - 15000
                p2 = track_config[index + 1].total_cost
                if p1 < p2:
                    swap_to_end(index, track_config)
                    continue


def swap_to_end(index, track_config):
    while index < len(track_config) - 1:
        if track_config[index + 1].width == 0 or track_config[index + 1].height == 0:
            break
        track_config[index].day, track_config[index + 1].day = track_config[index + 1].day, track_config[index].day
        track_config[index], track_config[index + 1] = track_config[index + 1], track_config[index]

        index += 1
