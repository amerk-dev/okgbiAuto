from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from .core import reality_check
import models


def calculate_plan_min_retooling(spec: models.ProductionSpecification):
    """
    Расчёт №4 – вариант с минимальным количеством переналадок машины формировщика дорожки.
    Алгоритм старается использовать одинаковые настройки для последовательных дорожек.
    """
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    orders = spec.orders
    ready_plates = spec.ready_plates  # плиты, которые уже изготовлены
    need_create_plates, ready_plates = hasReadyPlate(orders, ready_plates)
    is_real = reality_check(need_create_plates, available_tracks, track_len)

    # Получаем конфигурацию дорожек по варианту минимизации переналадок
    res = bestPlatesMinRetooling(available_tracks, track_len, need_create_plates, spec.directory)
    retooling_cost = count_of_retooling(res, spec.directory.retooling.price)
    print(retooling_cost)
    return res, ready_plates, retooling_cost, is_real


def bestPlatesMinRetooling(trackDays, track_len: int, needPlates, prices):
    """
    Для минимизации переналадок пытаемся для каждой дорожки использовать тот же тип плит,
    что и в предыдущей дорожке (одинаковые: ширина, высота, concrete_class, wire_bottom, wire_top).
    Если выбранная ранее группа недоступна или не даёт заполнения, выбираем группу, которая
    обеспечивает максимальное заполнение дорожки. Таким образом, последовательные дорожки будут иметь
    одинаковые параметры, что снижает количество переналадок.
    """
    tracks_config = []

    # Функция группировки плит по ключу: (width, height, concrete_class, wire_bottom, wire_top)
    def group_plates(needPlates):
        groups = defaultdict(list)
        for order in needPlates:
            for plate in order["plate"]:
                if plate.count > 0:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    groups[key].append(plate)
        return groups

    # Алгоритм динамического программирования для группы однородных плит (задача о рюкзаке)
    def knapsack_for_group(capacity, items):
        # dp[w] = (заполненная длина, выбор плит: словарь {индекс_предмета: количество})
        dp = [(0, {}) for _ in range(capacity + 1)]
        for i, (length, count, plate_obj) in enumerate(items):
            for w in range(capacity, 0, -1):
                for k in range(1, count + 1):
                    used_length = k * length
                    if used_length > w:
                        break
                    prev_fill, prev_sel = dp[w - used_length]
                    candidate_fill = prev_fill + used_length
                    if candidate_fill > dp[w][0]:
                        new_sel = prev_sel.copy()
                        new_sel[i] = new_sel.get(i, 0) + k
                        dp[w] = (candidate_fill, new_sel)
        best = max(dp, key=lambda x: x[0])
        return best  # (filled_length, selection)

    prev_group_key = None  # сохраняем группу предыдущей дорожки для минимизации переналадок

    for track_day in trackDays:
        day = track_day.day
        while track_day.count > 0:
            groups = group_plates(needPlates)
            selected_group_key = None
            best_fill = 0
            best_selection = None

            # Если предыдущая группа доступна, сначала проверяем её
            if prev_group_key and prev_group_key in groups:
                group_items = sorted(
                    [(p.length, p.count, p) for p in groups[prev_group_key] if p.count > 0],
                    key=lambda x: x[0]
                )
                if group_items:
                    fill, selection = knapsack_for_group(track_len, group_items)
                    if fill > 0:
                        selected_group_key = prev_group_key
                        best_fill = fill
                        best_selection = selection

            # Если предыдущая группа не подходит или не выбрана, ищем оптимальную группу
            if not selected_group_key:
                for group_key, plates in groups.items():
                    group_items = sorted(
                        [(p.length, p.count, p) for p in plates if p.count > 0],
                        key=lambda x: x[0]
                    )
                    if not group_items:
                        continue
                    fill, selection = knapsack_for_group(track_len, group_items)
                    if fill > best_fill:
                        best_fill = fill
                        best_selection = selection
                        selected_group_key = group_key

            # Если ни одна группа дала положительный результат, прекращаем заполнение дорожки
            if not selected_group_key:
                break

            width, height, concrete_class, wire_bottom, wire_top = selected_group_key
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

            # Формируем список плит выбранной группы для применения решения DP
            group_plates_list = []
            for order in needPlates:
                for plate in order["plate"]:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    if key == selected_group_key and plate.count > 0:
                        group_plates_list.append(plate)
            group_plates_list.sort(key=lambda p: p.length)

            # Применяем выбор из DP для данной группы
            for idx, used_count in best_selection.items():
                try:
                    plate = group_plates_list[idx]
                except IndexError:
                    continue
                actual_used = min(used_count, plate.count)
                plate.count -= actual_used
                current_config.plates.extend([plate] * actual_used)

            # Расчёт затрат для заполненной части дорожки
            concrete_price = next((cc.price for cc in prices.concrete_classes if cc.name == concrete_class), 0)
            cost = 0
            for plate in current_config.plates:
                cost += wire_bottom * prices.wire.price
                cost += wire_top * prices.wire.price
                cost += (plate.length / 1000 * height / 1000 * width / 1000) * concrete_price
            current_config.total_cost = cost
            free_cost = ((current_config.free_len / 1000 * height / 1000 * width / 1000) * concrete_price)
            current_config.free_cost = free_cost
            current_config.full_cost = current_config.total_cost + current_config.free_cost

            tracks_config.append(current_config)
            track_day.count -= 1
            prev_group_key = selected_group_key  # запоминаем выбранную группу для следующей дорожки

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
