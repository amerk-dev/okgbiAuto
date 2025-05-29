from copy import deepcopy
from collections import defaultdict
import models
import time


def profile_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result

    return wrapper


@profile_time
def calculate_plan(spec: models.ProductionSpecification):
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    orders = spec.orders
    original_ready_plates = [deepcopy(plate) for plate in spec.ready_plates]
    ready_plates = [deepcopy(plate) for plate in spec.ready_plates]

    need_create_plates, updated_ready_plates = hasReadyPlate(orders, ready_plates)

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
            used_plate = deepcopy(original)
            used_plate.count = original.count
            used_ready_plates.append(used_plate)

    # Добавим order к использованным плитам по аналогии с соответствующими заказами
    for plate in used_ready_plates:
        for order in orders:
            for date in order.completion_dates:
                for p in date.plates:
                    if (plate.length == p.length and plate.width == p.width and plate.height == p.height and
                            plate.concrete_class == p.concrete_class and plate.wire_bottom == p.wire_bottom and plate.wire_top == p.wire_top):
                        plate.order = order.number

    is_real = reality_check(need_create_plates, available_tracks, track_len)
    tracks_config = bestPlates(available_tracks, track_len, need_create_plates, spec.directory)

    unplaced_plates = []
    for date_entry in need_create_plates:
        date = date_entry["date"]
        for plate in date_entry["plate"]:
            if plate.count > 0:
                unplaced_plates.append({
                    "date": date,
                    "plate": [deepcopy(plate)]
                })
    unplaced_plates_merged = merge_plates(unplaced_plates)

    retooling_cost = count_of_retooling(tracks_config, spec.directory.retooling.price)

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


def bestPlates(trackDay, track_len: int, needPlates, prices):
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
            plates_with_deadline.sort(key=lambda x: (x.width, x.height), reverse=True) #ToDo добавить высоту совсместно с шириной
            plates_without_deadline.sort(key=lambda x: (x.width, x.height), reverse=True)

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


def count_of_retooling(tracks, price) -> dict:
    if not tracks:
        return {
            "price": 0,
            "daily_retoolings": [],
            "last_state": None
        }

    # Группируем все дорожки по дням и собираем уникальные размеры для каждого дня
    daily_dimensions = defaultdict(set)
    for track in tracks:
        daily_dimensions[track.day].add((track.width, track.height))

    # Сортируем дни по порядку
    sorted_days = sorted(daily_dimensions.keys())
    daily_retoolings = []
    total_price = 0
    prev_dimensions = None

    for day in sorted_days:
        current_dimensions = daily_dimensions[day]

        if prev_dimensions is not None:  # Пропускаем первый день (нет предыдущего дня для сравнения)
            # Находим изменения между днями
            changes = []
            count = 0

            if not prev_dimensions:  # Если предыдущий день пустой (на всякий случай)
                count = len(current_dimensions)
                for curr in current_dimensions:
                    changes.append({
                        "from": None,
                        "to": {"width": curr[0], "height": curr[1]}
                    })
            else:
                # Если размеры изменились
                if prev_dimensions != current_dimensions:
                    # Находим общие размеры между днями
                    common = prev_dimensions & current_dimensions

                    if not common:
                        # Все размеры изменились - полная переналадка
                        count = len(current_dimensions)
                        for curr in current_dimensions:
                            changes.append({
                                "from": {"width": next(iter(prev_dimensions))[0],
                                         "height": next(iter(prev_dimensions))[1]},
                                "to": {"width": curr[0], "height": curr[1]}
                            })
                    else:
                        # Переналадка только для новых размеров
                        count = len(current_dimensions - common)
                        for curr in (current_dimensions - common):
                            changes.append({
                                "from": {"width": next(iter(prev_dimensions))[0],
                                         "height": next(iter(prev_dimensions))[1]},
                                "to": {"width": curr[0], "height": curr[1]}
                            })

            if count > 0:
                daily_retoolings.append({
                    "date": day,
                    "count": count,
                    "price": count * price,
                    "changes": changes
                })
                total_price += count * price

        prev_dimensions = current_dimensions

    last_state = {
        "width": tracks[-1].width,
        "height": tracks[-1].height
    }

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
        cost += (((plate.length * track_config.height * track_config.width) / 10**9) * concrete_price) * 0.65
    cost += 85000 / 1000 * prices.wire.price * (
            track_config.wire_bottom + track_config.wire_top) #ToDo вынести 85000 в конфиг или еще что-то

    total_cost = cost

    free_vol = track_config.free_len / 1000 * track_config.height / 1000 * track_config.width / 1000
    free_cost = free_vol * concrete_price
    full_cost = total_cost + free_cost

    return total_cost, free_cost, full_cost
