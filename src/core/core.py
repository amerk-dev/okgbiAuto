from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import models
from copy import deepcopy


def calculate_plan(spec: models.ProductionSpecification):
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
    tracks_config = bestPlates(available_tracks, track_len, need_create_plates, spec.directory)

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


def reality_check(plates, tracks, track_len):
    all_plates_len = 0
    all_track_len = 0
    for date in plates:
        for plate in date["plate"]:
            all_plates_len += (plate.count * plate.length)

    for track in tracks:
        all_track_len += (track.count * track_len)

    return True if all_plates_len < all_track_len else False


def hasReadyPlate(orders: List[models.Order], plates: models.PlateSpecification):
    tmp_need_plates = []
    for order in orders:
        for date in order.completion_dates:
            tmp_need_plates.append({
                "date": date.date,
                "plate": date.plates
            })

    for tnp in tmp_need_plates:
        for i in plates:
            if tnp["plate"][0].length == i.length and tnp["plate"][0].width == i.width and tnp["plate"][
                0].height == i.height:
                deduct = min(tnp["plate"][0].count, i.count)
                tnp["plate"][0].count -= deduct
                i.count -= deduct

    res = []
    for order in tmp_need_plates:
        filtered_plates = [plate for plate in order["plate"] if plate.count != 0]

        if filtered_plates:
            res.append({
                "date": order["date"],
                "plate": filtered_plates
            })

    # Это если на одну дату разные заказы, чтобы их совместить в одну дату
    grouped = defaultdict(list)
    for item in res:
        date_key = item["date"]
        grouped[date_key].extend(item["plate"])

    result = [
        {"date": date, "plate": plates}
        for date, plates in grouped.items()
    ]

    resres = merge_plates(result)
    return resres, plates


def merge_plates(tmp_need_plates):
    date_group = defaultdict(lambda: defaultdict(int))

    for order in tmp_need_plates:
        for plate in order["plate"]:
            if plate.count == 0:
                continue

            plate_key = (
                plate.length,
                plate.width,
                plate.height,
                plate.concrete_class,  # Используем имя поля модели
                plate.wire_bottom,
                plate.wire_top
            )
            date_group[order["date"]][plate_key] += plate.count

    result = []
    for date, plates in date_group.items():
        plate_list = []
        for params, total_count in plates.items():
            # Формируем данные с использованием алиаса 'class'
            plate_data = {
                "count": total_count,
                "length": params[0],
                "width": params[1],
                "height": params[2],
                "class": params[3],  # Важно: используем алиас!
                "wire_bottom": params[4],
                "wire_top": params[5]
            }
            plate_list.append(models.PlateSpecification(**plate_data))
        result.append({"date": date, "plate": plate_list})

    return result


# bestPlates Используется для поиска лучших плит под дорожки на определенный день
def bestPlates(trackDay, track_len: int, needPlates, prices):
    tracks_config = []
    # Проходим по всем трекам дня
    for tracks in trackDay:
        for track in range(tracks.count):

            # Подготовка для нового трека
            track_remaining = track_len
            current_config = None
            available_size = None
            concrete_price = None

            # Сортируем пластины по убыванию длины для оптимального заполнения
            sorted_plates = sorted(
                (plate for plate_last_day in needPlates for plate in plate_last_day["plate"] if plate.count > 0),
                key=lambda x: x.length,
                reverse=True
            )

            # Обрабатываем пластины для текущего трека
            for plate in sorted_plates:
                if track_remaining <= 0:
                    break  # Трек полностью заполнен

                # Проверяем совместимость размеров
                if current_config:
                    # Для последующих пластин размер должен совпадать с первой
                    if (plate.width, plate.height) != available_size:
                        continue
                else:
                    # Инициализируем новую конфигурацию для первой пластины
                    current_config = models.TrackConfig(
                        day=tracks.day,
                        height=plate.height,
                        width=plate.width,
                        free_len=track_len,
                        useful_len=0,
                        concrete_class=plate.concrete_class,
                        wire_bottom=plate.wire_bottom,
                        wire_top=plate.wire_top,
                        total_cost=0,
                        plates=[]
                    )
                    available_size = (plate.width, plate.height)
                    tracks_config.append(current_config)

                # Добавляем пластины пока есть место
                max_plates = min(plate.count, track_remaining // plate.length)
                if max_plates > 0:
                    current_config.plates.extend([plate] * max_plates)
                    current_config.free_len -= plate.length * max_plates
                    current_config.useful_len += plate.length * max_plates
                    plate.count -= max_plates
                    track_remaining -= plate.length * max_plates
                    # Расчет стоимости
                    concrete_price = next(
                        cc.price
                        for cc in prices.concrete_classes
                        if cc.name == current_config.concrete_class
                    )
                    cost = 0
                    cost += current_config.wire_bottom * prices.wire.price * max_plates
                    cost += current_config.wire_top * prices.wire.price * max_plates
                    cost += (
                                    plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000
                            ) * concrete_price

                    current_config.total_cost = cost

                free_cost = ((current_config.free_len / 1000 * current_config.height / 1000
                              * current_config.width / 1000) * concrete_price)
                current_config.free_cost = free_cost
                current_config.full_cost = current_config.free_cost + current_config.total_cost
        # Уменьшаем количество доступных треков
        tracks.count -= 1

    return tracks_config


def count_of_retooling(tracks: List[models.TrackConfig], price) -> int:
    if not tracks:
        return 0

    retooling_count = 0
    prev_width = None
    prev_height = None

    for track in tracks:
        current_width = track.width
        current_height = track.height

        if prev_width is not None and prev_height is not None:
            if current_width != prev_width or current_height != prev_height:
                retooling_count += 1

        prev_width = current_width
        prev_height = current_height

    return retooling_count * price

