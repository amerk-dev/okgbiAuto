from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check
import models

def calculate_plan_min_mix(spec: models.ProductionSpecification):
    """
    Расчёт №3 – вариант с минимальным смешиванием плит по классу бетона и проволоке.
    """
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    orders = spec.orders
    ready_plates = spec.ready_plates  # плиты, которые уже изготовлены
    need_create_plates, ready_plates = hasReadyPlate(orders, ready_plates)
    is_real = reality_check(need_create_plates, available_tracks, track_len)

# Получаем конфигурацию дорожек по варианту с минимальным смешиванием
    res = bestPlatesMinMix(available_tracks, track_len, need_create_plates, spec.directory)
    retooling_cost = count_of_retooling(res, spec.directory.retooling.price)
    print(retooling_cost)
    return res, ready_plates, retooling_cost, is_real


def bestPlatesMinMix(trackDays, track_len: int, needPlates, prices):
    """
    Для каждой дорожки выбирается однородная группа плит (одинаковый класс бетона и проводка),
    которая обеспечивает максимально возможное заполнение дорожки при минимальном использовании более дорогих материалов.
    Если заполнение достигает не менее 80% д  лины дорожки, вариант считается приемлемым.
    """
    tracks_config = []

    # Группируем плиты по ключу: (width, height, concrete_class, wire_bottom, wire_top)
    def group_plates(needPlates):
        groups = defaultdict(list)
        for order in needPlates:
            for plate in order["plate"]:
                if plate.count > 0:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    groups[key].append(plate)
        return groups

    # Задача о рюкзаке для группы (однородных плит)
    def knapsack_homogeneous(capacity, items):
        # items: список кортежей (length, count, plate_obj)
        dp = [(0, {}) for _ in range(capacity + 1)]
        for i, (length, count, plate_obj) in enumerate(items):
            for w in range(capacity, 0, -1):
                for k in range(1, count + 1):
                    cost = k * length
                    if cost > w:
                        break
                    prev_fill, prev_sel = dp[w - cost]
                    candidate_fill = prev_fill + cost
                    if candidate_fill > dp[w][0]:
                        new_sel = prev_sel.copy()
                        new_sel[i] = new_sel.get(i, 0) + k
                        dp[w] = (candidate_fill, new_sel)
        best = max(dp, key=lambda x: x[0])
        return best  # (filled_length, selection)

    # Обрабатываем дорожки по дням
    for track_day in trackDays:
        day = track_day.day
        while track_day.count > 0:
            best_config = None
            best_fill = 0
            best_cost = None  # суммарная стоимость заполнения выбранной группы
            best_group_key = None
            best_selection = None

            groups = group_plates(needPlates)
            # Перебираем однородные группы
            for group_key, plates in groups.items():
                # Подготовка предметов для DP: (length, count, plate_obj)
                items = []
                # Для обеспечения корректности – сортируем плиты по длине
                sorted_group = sorted([p for p in plates if p.count > 0], key=lambda p: p.length)
                for plate in sorted_group:
                    items.append((plate.length, plate.count, plate))
                if not items:
                    continue

                fill, selection = knapsack_homogeneous(track_len, items)
                if fill <= 0:
                    continue

                # Расчет стоимости заполненной части:
                # стоимость рассчитывается по каждому использованному элементу
                concrete_price = next(
                    (cc.price for cc in prices.concrete_classes if cc.name == group_key[2]), 0
                )
                cost = 0
                # Для каждого выбранного предмета (индекс в отсортированном списке)
                for idx, used_count in selection.items():
                    plate = sorted_group[idx]
                    cost += group_key[3] * prices.wire.price * used_count  # проволока снизу
                    cost += group_key[4] * prices.wire.price * used_count  # проволока сверху
                    cost += (plate.length / 1000 * group_key[1] / 1000 * group_key[0] / 1000) * concrete_price * used_count
                # Если заполнение не менее 80% дорожки, вариант считается предпочтительным
                if fill >= 0.8 * track_len:
                    # Выбираем вариант с минимальной стоимостью среди вариантов с достаточным заполнением
                    if (best_config is None) or (fill > best_fill) or (fill == best_fill and cost < best_cost):
                        best_fill = fill
                        best_cost = cost
                        best_group_key = group_key
                        best_selection = selection

            # Если ни одна однородная группа не дала заполнения не менее 80%,
            # выбираем вариант с максимальным заполнением (даже если смешивание не происходит)
            if best_group_key is None:
                for group_key, plates in groups.items():
                    items = []
                    sorted_group = sorted([p for p in plates if p.count > 0], key=lambda p: p.length)
                    for plate in sorted_group:
                        items.append((plate.length, plate.count, plate))
                    if not items:
                        continue
                    fill, selection = knapsack_homogeneous(track_len, items)
                    if fill > best_fill:
                        concrete_price = next(
                            (cc.price for cc in prices.concrete_classes if cc.name == group_key[2]), 0
                        )
                        cost = 0
                        for idx, used_count in selection.items():
                            plate = sorted_group[idx]
                            cost += group_key[3] * prices.wire.price * used_count
                            cost += group_key[4] * prices.wire.price * used_count
                            cost += (plate.length / 1000 * group_key[1] / 1000 * group_key[0] / 1000) * concrete_price * used_count
                        best_fill = fill
                        best_cost = cost
                        best_group_key = group_key
                        best_selection = selection

            # Если так и не нашли подходящую группу, завершаем заполнение дорожки
            if best_group_key is None:
                break

            # Формируем конфигурацию дорожки с выбранной группой
            width, height, concrete_class, wire_bottom, wire_top = best_group_key
            current_config = models.TrackConfig(
                day=day,
                height=height,
                width=width,
                free_len=track_len - best_fill,
                useful_len=best_fill,
                concrete_class=concrete_class,
                wire_bottom=wire_bottom,
                wire_top=wire_top,
                total_cost=0,
                plates=[]
            )
            # Применяем выбор DP для данной группы
            group_plates_list = []
            for order in needPlates:
                for plate in order["plate"]:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    if key == best_group_key and plate.count > 0:
                        group_plates_list.append(plate)
            group_plates_list.sort(key=lambda p: p.length)
            for idx, used_count in best_selection.items():
                try:
                    plate = group_plates_list[idx]
                except IndexError:
                    continue
                actual_used = min(used_count, plate.count)
                plate.count -= actual_used
                current_config.plates.extend([plate] * actual_used)

            # Расчёт итоговой стоимости дорожки
            concrete_price = next(
                (cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class), 0
            )
            cost = 0
            for plate in current_config.plates:
                cost += current_config.wire_bottom * prices.wire.price
                cost += current_config.wire_top * prices.wire.price
                cost += (plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000) * concrete_price
            current_config.total_cost = cost
            free_cost = ((current_config.free_len / 1000 * current_config.height / 1000 *
                          current_config.width / 1000) * concrete_price)
            current_config.free_cost = free_cost
            current_config.full_cost = current_config.total_cost + current_config.free_cost

            tracks_config.append(current_config)
            track_day.count -= 1

    return tracks_config



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
