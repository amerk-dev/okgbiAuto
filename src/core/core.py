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


def bestPlates(trackDay, track_len: int, needPlates, prices):
    tracks_config = []
    global_plates_with_deadline=[]
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
                        global_plates_with_deadline.append(plate)
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

                    current_config.total_cost, current_config.free_cost, current_config.full_cost = calculate_price(
                        current_config, prices)

        tracks.count -= 1

    post_calculating(tracks_config, global_plates_with_deadline)

    return tracks_config


def count_of_retooling(tracks, price,
                       retooler) -> dict:  # ToDo  переделать/оптимизировать (порядок дорожек в течении дня не важен)
    if not tracks:
        return {
            "price": 0,
            "daily_retoolings": [],
            "last_state": None
        }

    daily_changes = defaultdict(list)
    prev_track = retooler

    for current_track in tracks:
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
    total_count = sum(len(changes) for changes in daily_changes.values())
    total_price = total_count * price

    for date in sorted_dates:
        changes = daily_changes[date]
        daily_retoolings.append({
            "date": date,
            "count": len(changes),
            "price": len(changes) * price,
            "changes": changes
        })

    last_state = {
        "width": prev_track.width,
        "height": prev_track.height
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
    cost += 85000 / 1000 * prices.wire.price * (
            track_config.wire_bottom + track_config.wire_top)  # ToDo вынести 85000 в конфиг или еще что-то

    total_cost = cost

    free_vol = track_config.free_len / 1000 * track_config.height / 1000 * track_config.width / 1000
    free_cost = free_vol * concrete_price
    full_cost = total_cost + free_cost

    return total_cost, free_cost, full_cost


def post_calculating(track_config, plates_with_deadline):
    for index in range(len(track_config)-1):
        track = track_config[index]
        if track.width != track_config[index + 1].width or track.height != track_config[index + 1].height:
            for plate in track.plates:
                if plate in plates_with_deadline:
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
