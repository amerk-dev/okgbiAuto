import datetime
import difflib
from copy import deepcopy
from collections import defaultdict
from datetime import date
from itertools import chain
from typing import List, Tuple, Optional, Dict

import models
import time


def profile_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result

    return wrapper


TRACK_LENGTH = 85000
TAIL_LENGTH = 2000


@profile_time
def calculate_plan(spec: models.ProductionSpecification):
    global TRACK_LENGTH
    TRACK_LENGTH = spec.directory.track.length
    global TAIL_LENGTH
    TAIL_LENGTH = spec.directory.tail_len
    available_tracks = spec.available_tracks
    orders = spec.orders
    original_ready_plates = [deepcopy(plate) for plate in spec.ready_plates]
    ready_plates = [deepcopy(plate) for plate in spec.ready_plates]

    # Вычитаем готовые плиты со склада из общей потребности
    need_create_plates, updated_ready_plates = hasReadyPlate(orders, ready_plates)

    # Определяем, какие именно готовые плиты были использованы
    used_ready_plates = []
    for original in original_ready_plates:
        updated = next(
            (p for p in updated_ready_plates
             if (p.length == original.length and p.width == original.width and p.height == original.height and
                 p.concrete_class == original.concrete_class and p.wire_bottom == original.wire_bottom and
                 p.wire_top == original.wire_top)),
            None
        )
        used_count = original.count
        if updated:
            used_count -= updated.count

        if used_count > 0:
            used_plate = deepcopy(original)
            used_plate.count = used_count
            used_ready_plates.append(used_plate)

    # Присваиваем номер заказа использованным плитам
    for plate in used_ready_plates:
        if plate.order: continue
        for order in orders:
            for c_date in order.completion_dates:
                for p in c_date.plates:
                    if (plate.length == p.length and plate.width == p.width and plate.height == p.height and
                            plate.concrete_class == p.concrete_class and plate.wire_bottom == p.wire_bottom and plate.wire_top == p.wire_top):
                        plate.order = order.number
                        break
            if plate.order:
                break

    # Проверяем, достаточно ли теоретически дорожек для производства
    is_real = reality_check(need_create_plates, available_tracks, TRACK_LENGTH)

    # Создаем производственный план
    tracks_config = bestPlates(available_tracks, TRACK_LENGTH, need_create_plates, spec.directory, spec)

    # ПОДСЧЕТ НЕРАЗМЕЩЕННЫХ ПЛИТ
    placed_counts = defaultdict(int)
    for track_conf in tracks_config:
        for p in track_conf.plates:
            # Создаем уникальный ключ для каждого типа плиты
            plate_key = (p.length, p.width, p.height, p.concrete_class, p.wire_bottom, p.wire_top, p.name, p.order)
            placed_counts[plate_key] += 1  # В плане у каждой плиты count=1

    # Сравниваем потребность с тем, что разместили
    unplaced_plates_data = []
    for date_entry in need_create_plates:
        unplaced_for_date = []
        for required_plate in date_entry["plate"]:
            plate_key = (required_plate.length, required_plate.width, required_plate.height,
                         required_plate.concrete_class, required_plate.wire_bottom, required_plate.wire_top,
                         required_plate.name, required_plate.order)

            num_required = required_plate.count
            num_placed = placed_counts.get(plate_key, 0)

            num_unplaced = num_required - num_placed

            if num_unplaced > 0:
                unplaced_plate = deepcopy(required_plate)
                unplaced_plate.count = num_unplaced
                unplaced_for_date.append(unplaced_plate)

                placed_counts[plate_key] = 0

        if unplaced_for_date:
            unplaced_plates_data.append({"date": date_entry["date"], "plate": unplaced_for_date})

    unplaced_plates_merged = merge_plates(unplaced_plates_data)

    retooling_cost = count_of_retooling(tracks_config, spec.directory.retooling.price, spec.retooler)

    return (
        tracks_config,
        used_ready_plates,
        unplaced_plates_merged,
        updated_ready_plates,
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


def hasReadyPlate(orders, plates):
    tmp_need_plates = []
    for order in orders:
        for date in order.completion_dates:
            for p in date.plates:
                p.order = order.number  # Устанавливаем номер заказа
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

    grouped = defaultdict(list)
    for item in res:
        grouped[item["date"]].extend(item["plate"])

    result = [
        {"date": date, "plate": plates}
        for date, plates in grouped.items()
    ]

    resres = merge_plates(result)
    return resres, plates


def merge_plates(tmp_need_plates):
    date_group = defaultdict(lambda: defaultdict(lambda: {"count": 0, "plate": None}))

    for order in tmp_need_plates:
        for plate in order["plate"]:
            if plate.count == 0:
                continue

            plate_key = (
                plate.length,
                plate.width,
                plate.height,
                plate.concrete_class,
                plate.wire_bottom,
                plate.wire_top,
                plate.name,
                plate.order
            )

            if date_group[order["date"]][plate_key]["plate"] is None:
                date_group[order["date"]][plate_key]["plate"] = deepcopy(plate)
                date_group[order["date"]][plate_key]["plate"].count = 0

            date_group[order["date"]][plate_key]["plate"].count += plate.count

    result = []
    for date, plates in date_group.items():
        plate_list = [p_data["plate"] for p_data in plates.values() if p_data["plate"].count > 0]
        result.append({"date": date, "plate": plate_list})

    return result


def bestPlates(
        trackDay: List[models.AvailableTrack],
        track_len: int,
        needPlates: List[Dict],
        directory: models.Directory,
        spec: models.ProductionSpecification
) -> List[models.TrackConfig]:
    """
    Размещает плиты по дорожкам с приоритетом на плиты с дедлайном.
    """
    tracks_config = []

    all_plates_to_produce: List[Tuple[Optional[date], models.PlateSpecification]] = []
    for item in needPlates:
        for plate in item['plate']:
            all_plates_to_produce.append((item.get('date'), deepcopy(plate)))

    deadline_items = sorted(
        [item for item in all_plates_to_produce if item[0] is not None],
        key=lambda item: (item[0], -item[1].width, -item[1].height)  # Сначала дата, потом размер
    )
    deadline_items_copy = deadline_items  # для постобработки
    filler_items = sorted(
        [item for item in all_plates_to_produce if item[0] is None],
        key=lambda item: (-item[1].width, -item[1].height)  # Просто по размеру
    )

    available_tracks_iterator = iter(
        (d.day) for d in sorted(trackDay, key=lambda x: x.day) for _ in range(d.count)
    )

    while deadline_items or filler_items:
        try:
            current_day = next(available_tracks_iterator)
        except StopIteration:
            break  # Дорожки закончились

        anchor_item = deadline_items[0] if deadline_items else filler_items[0]
        anchor_plate = anchor_item[1]
        target_size = (anchor_plate.width, anchor_plate.height)

        same_size_plates = [
            item[1] for item in chain(deadline_items, filler_items)
            if (item[1].width, item[1].height) == target_size
        ]

        if not same_size_plates:
            continue  # На всякий случай, если что-то пошло не так

        concrete_class = max(same_size_plates, key=lambda plate: same_size_plates).concrete_class

        current_config = models.TrackConfig(
            day=current_day,
            width=anchor_plate.width,
            height=anchor_plate.height,
            concrete_class=concrete_class,
            wire_bottom=0,
            wire_top=0,
            free_len=track_len,
            useful_len=0,
            total_cost=0,
            plates=[]
        )
        tracks_config.append(current_config)

        track_remaining = track_len

        def place_plates_on_track(item_list: List[Tuple[Optional[date], models.PlateSpecification]]):
            nonlocal track_remaining
            for _, plate in item_list:
                if track_remaining <= 0: return
                if plate.count > 0 and (plate.width, plate.height) == target_size:
                    if plate.length == 0: continue  # Защита от деления на ноль

                    max_plates = min(plate.count, track_remaining // plate.length)
                    if max_plates > 0:
                        # Добавляем каждую плиту отдельно, чтобы сохранить информацию о заказе
                        for _ in range(max_plates):
                            plate_instance = deepcopy(plate)
                            plate_instance.count = 1
                            current_config.plates.append(plate_instance)

                        current_config.free_len -= plate.length * max_plates
                        current_config.useful_len += plate.length * max_plates
                        plate.count -= max_plates
                        track_remaining -= plate.length * max_plates

        place_plates_on_track(deadline_items)
        place_plates_on_track(filler_items)

        deadline_items = [item for item in deadline_items if item[1].count > 0]
        filler_items = [item for item in filler_items if item[1].count > 0]
        for plate in current_config.plates:
            current_config.wire_top = max(current_config.wire_top, plate.wire_top)
            current_config.wire_bottom = max(current_config.wire_bottom, plate.wire_bottom)

        current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(
            current_config, directory)

    c = 1
    track_history = []
    max_iterations = 30
    while c <= max_iterations:
        current_state = deepcopy(tracks_config)
        track_history.append(current_state)

        post_calculating(tracks_config, deadline_items_copy, spec)

        # Проверяем, не повторяется ли состояние через одну итерацию
        if len(track_history) >= 3 and compare_nested_lists(track_history[-3], track_history[-1]):
            break

        c += 1
    sorted_tracks_config = sort_by_width_and_height(tracks_config)
    return sorted_tracks_config


def compare_nested_lists(list1, list2):
    # Если оба объекта не являются списками, просто сравниваем их
    if not isinstance(list1, list) and not isinstance(list2, list):
        return list1 == list2

    # Если один из объектов список, а другой нет - они не равны
    if isinstance(list1, list) != isinstance(list2, list):
        return False

    # Если оба списка, сравниваем их длину
    if len(list1) != len(list2):
        return False

    # Рекурсивно сравниваем элементы списков
    for item1, item2 in zip(list1, list2):
        if not compare_nested_lists(item1, item2):
            return False

    return True

def count_of_retooling(tracks, price, retooler) -> dict:
    """
    Рассчитывает стоимость и количество переналадок с условием,
    что в начале каждого нового дня оснастка считается снятой
    (т.е. сравнение идет с исходным состоянием 'retooler').
    """
    if not tracks:
        return {
            "price": 0,
            "daily_retoolings": [],
            "last_state": None
        }
    daily_changes = defaultdict(list)
    prev_track = retooler

    for current_track in tracks:
        if prev_track is not retooler and current_track.day != prev_track.day:
            prev_track = retooler
        retooler.width, retooler.height = 0, 0
        # Основная проверка на необходимость переналадки
        if prev_track.width != current_track.width or prev_track.height != current_track.height:
            change_date = current_track.day
            daily_changes[change_date].append({
                "from": {
                    "width": prev_track.width,
                    "height": prev_track.height
                },
                "to": {
                    "width": current_track.width,
                    "height": current_track.height
                }
            })
        prev_track = current_track

    sorted_dates = sorted(daily_changes.keys())
    daily_retoolings = []
    total_count = sum(len(changes[:-1]) for changes in daily_changes.values())
    total_price = total_count * price

    for date in sorted_dates:
        changes = daily_changes[date]
        daily_retoolings.append({
            "date": date,
            "count": len(changes) - 1,
            "price": (len(changes) - 1) * price,
            "changes": changes
        })

    last_state = {
        "width": tracks[-1].width,
        "height": tracks[-1].height
    } if tracks else None

    return {
        "price": total_price,
        "daily_retoolings": daily_retoolings,
        "last_state": last_state
    }


def calculate_price(track_config, prices):
    cost = 0
    concrete_price = next(
        cc.price for cc in prices.concrete_classes if cc.name == track_config.concrete_class
    )

    for plate in track_config.plates:
        cost += (((plate.length * track_config.height * track_config.width) / 10 ** 9) * concrete_price) * 0.65
    cost += TRACK_LENGTH / 1000 * prices.wire.price * (
            track_config.wire_bottom + track_config.wire_top)

    total_cost = cost

    free_vol = track_config.free_len / 1000 * track_config.height / 1000 * track_config.width / 1000
    free_cost = free_vol * concrete_price
    full_cost = total_cost + free_cost

    return total_cost, free_cost, full_cost


def post_calculating(track_config, plates_with_date, spec: models.ProductionSpecification):
    for index in range(len(track_config) - 1):
        track = track_config[index]
        if spec.directory.force_tail == 0:
            if track.width != track_config[index + 1].width or track.height != track_config[index + 1].height:
                found_plate_with_deadline = False
                for plate in track.plates:
                    for deadline_plate in plates_with_date:
                        if (plate.name == deadline_plate[1].name and plate.length == deadline_plate[
                            1].length and plate.width == deadline_plate[1].width
                                and plate.height == deadline_plate[1].height and plate.concrete_class == deadline_plate[
                                    1].concrete_class and plate.wire_top == deadline_plate[
                                    1].wire_top and plate.wire_bottom == deadline_plate[
                                    1].wire_bottom and plate.order == deadline_plate[1].order
                        ):
                            found_plate_with_deadline = True
                            break
                    if found_plate_with_deadline:
                        break

                if not found_plate_with_deadline:
                    if track.free_len > TAIL_LENGTH:
                        swap_to_end(index, track_config)
                        continue
        elif spec.directory.force_tail == 1:
            found_plate_with_deadline = False
            for plate in track.plates:
                for deadline_plate in plates_with_date:
                    if (plate.name == deadline_plate[1].name and plate.length == deadline_plate[
                        1].length and plate.width == deadline_plate[1].width
                            and plate.height == deadline_plate[1].height and plate.concrete_class == deadline_plate[
                                1].concrete_class and plate.wire_top == deadline_plate[
                                1].wire_top and plate.wire_bottom == deadline_plate[1].wire_bottom and plate.order ==
                            deadline_plate[1].order
                    ):
                        found_plate_with_deadline = True
                        break
                if found_plate_with_deadline:
                    break

            if not found_plate_with_deadline:
                if track.free_len > TAIL_LENGTH:
                    swap_to_end(index, track_config)
                    continue

        elif spec.directory.force_tail == 2:
            if track.free_len > TAIL_LENGTH:
                swap_to_deadline(index, track_config, spec)


def swap_to_end(index, track_config):
    while index < len(track_config) - 1:
        if track_config[index + 1].width == 0 or track_config[index + 1].height == 0:
            break
        track_config[index].day, track_config[index + 1].day = track_config[index + 1].day, track_config[index].day
        track_config[index], track_config[index + 1] = track_config[index + 1], track_config[index]

        index += 1


def swap_to_deadline(index, track_config, spec: models.ProductionSpecification):
    current_day_str = track_config[index].day
    current_day = date.fromisoformat(current_day_str) if isinstance(current_day_str, str) else current_day_str
    deadline = last_day_for_plate(track_config[index], spec, track_config)

    while current_day < deadline:
        if track_config[index + 1].width == 0 or track_config[index + 1].height == 0:
            break
        track_config[index].day, track_config[index + 1].day = track_config[index + 1].day, track_config[index].day
        track_config[index], track_config[index + 1] = track_config[index + 1], track_config[index]

        current_day_str = track_config[index].day
        current_day = date.fromisoformat(current_day_str) if isinstance(current_day_str, str) else current_day_str
        index += 1


def last_day_for_plate(track, spec: models.ProductionSpecification, track_config):
    last_track_day = track_config[-1].day
    for plate in track.plates:
        plate_deadline = get_plate_deadline(plate, spec)
        if plate_deadline is not None:
            last_track_day = min(last_track_day, plate_deadline)
    return last_track_day


def get_plate_deadline(plate, spec: models.ProductionSpecification):
    for order in spec.orders:
        if plate.order == order.number:
            for ord_dates in order.completion_dates:
                for ord_plates in ord_dates.plates:
                    if (plate.length == ord_plates.length and
                            plate.width == ord_plates.width and
                            plate.height == ord_plates.height and
                            plate.concrete_class == ord_plates.concrete_class and
                            plate.wire_bottom == ord_plates.wire_bottom and
                            plate.wire_top == ord_plates.wire_top):
                        return ord_dates.date
    return None


def sort_by_width_and_height(track_config):
    return sorted(track_config, key=lambda x: (x.day, x.width, x.height))