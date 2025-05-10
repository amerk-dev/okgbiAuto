from copy import deepcopy
from collections import defaultdict
import models


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
        for track in range(tracks.count):
            track_remaining = track_len
            current_config = None
            available_size = None
            concrete_price = None

            sorted_plates = sorted(
                (plate for plate_last_day in needPlates for plate in plate_last_day["plate"] if plate.count > 0),
                key=lambda x: x.length,
                reverse=True
            )

            for plate in sorted_plates:
                if track_remaining <= 0:
                    break

                if current_config:
                    if (plate.width, plate.height) != available_size:
                        continue
                else:
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

                max_plates = min(plate.count, track_remaining // plate.length)
                if max_plates > 0:
                    for _ in range(max_plates):
                        current_config.plates.append(deepcopy(plate))
                    current_config.free_len -= plate.length * max_plates
                    current_config.useful_len += plate.length * max_plates
                    plate.count -= max_plates
                    track_remaining -= plate.length * max_plates

                    concrete_price = next(
                        cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class
                    )
                    cost = 0
                    cost += current_config.wire_bottom * prices.wire.price * max_plates
                    cost += current_config.wire_top * prices.wire.price * max_plates
                    cost += (
                                    plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000
                            ) * concrete_price * max_plates

                    current_config.total_cost = cost

                free_cost = (
                        (current_config.free_len / 1000 * current_config.height / 1000 * current_config.width / 1000)
                        * concrete_price
                ) if concrete_price else 0
                current_config.free_cost = free_cost
                current_config.full_cost = current_config.free_cost + current_config.total_cost

        tracks.count -= 1

    return tracks_config


def count_of_retooling(tracks, price) -> dict:
    if not tracks:
        return {
            "price": 0,
            "daily_retoolings": [],
            "last_state": None
        }

    daily_changes = defaultdict(list)
    prev_track = tracks[0]

    for current_track in tracks[1:]:
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