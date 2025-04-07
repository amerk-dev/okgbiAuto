from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import models


def calculate_plan_max_fill(spec: models.ProductionSpecification):
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    orders = spec.orders
    ready_plates = spec.ready_plates  # уже изготовленные плиты
    need_create_plates, ready_plates = hasReadyPlate(orders, ready_plates)
    # Получаем конфигурацию с максимальным заполнением дорожек
    res = bestPlatesMaxFill(available_tracks, track_len, need_create_plates, spec.directory)
    retooling_cost = count_of_retooling(res, spec.directory.retooling.price)
    print(retooling_cost)
    return res, ready_plates, retooling_cost


def bestPlatesMaxFill(trackDays, track_len: int, needPlates, prices):
    """
    Для каждой дорожки ищется такая группа совместимых плит (по ширине, высоте, классу и проводам),
    для которой с помощью алгоритма динамического программирования (задача о рюкзаке) можно максимально заполнить дорожку.
    """
    tracks_config = []

    # Функция для группировки плит по совместимым параметрам
    def group_plates(needPlates):
        # Группируем по (width, height, concrete_class, wire_bottom, wire_top)
        groups = defaultdict(list)
        for order in needPlates:
            for plate in order["plate"]:
                if plate.count > 0:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    groups[key].append(plate)
        return groups

    # Алгоритм динамического программирования для задачи с ограниченным количеством предметов.
    # Каждый предмет характеризуется: длиной, количеством и ссылкой на объект плиты.
    def knapsack_max_fill(capacity, items):
        # dp[w] = (max_fill, selection) где selection – словарь: индекс элемента -> количество выбранных плит
        dp = [(0, {}) for _ in range(capacity + 1)]
        for i, (length, count, plate_obj) in enumerate(items):
            for w in range(capacity, 0, -1):
                # Перебираем возможное количество плит данного типа от 1 до count
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
        # Находим лучшее заполнение (максимальное заполнение, не превосходящее capacity)
        best = max(dp, key=lambda x: x[0])
        return best

    # Обработка дорожек по дням (trackDays – список объектов с атрибутами day и count)
    for track_day in trackDays:
        day = track_day.day
        while track_day.count > 0:
            track_remaining = track_len
            best_config = None
            best_fill = 0
            best_group_key = None
            best_selection = None

            # Группируем доступные плиты по совместимым параметрам
            groups = group_plates(needPlates)
            # Перебираем каждую группу плит, чтобы найти наилучшее заполнение дорожки
            for group_key, plates in groups.items():
                # Подготавливаем список предметов для рюкзака: (length, count, plate_obj)
                items = []
                for plate in plates:
                    if plate.count > 0:
                        items.append((plate.length, plate.count, plate))
                if not items:
                    continue
                fill, selection = knapsack_max_fill(track_remaining, items)
                if fill > best_fill:
                    best_fill = fill
                    best_group_key = group_key
                    best_selection = selection

            # Если ни одна группа не смогла заполнить дорожку (например, закончились плиты)
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

            # Применяем выбранное решение: уменьшаем количество плит в группах и добавляем в конфигурацию
            # Для доступа к элементам выбранной группы надо собрать список индексов соответствующих плит
            # Из группы best_group_key, формируем список уникальных плит
            group_plates_list = []
            for order in needPlates:
                for plate in order["plate"]:
                    key = (plate.width, plate.height, plate.concrete_class, plate.wire_bottom, plate.wire_top)
                    if key == best_group_key and plate.count > 0:
                        group_plates_list.append(plate)
            # Сортируем список по длине для сопоставления с DP (порядок должен совпадать с items)
            group_plates_list.sort(key=lambda p: p.length)
            # Построим соответствие: индекс в items -> plate в отсортированном списке
            # Применяем выбор из DP
            for idx, used_count in best_selection.items():
                # Так как в items порядок соответствует отсортированному списку, выбираем плиту по индексу idx
                try:
                    plate = group_plates_list[idx]
                except IndexError:
                    continue
                # Уменьшаем количество доступных плит
                if used_count > plate.count:
                    used_count = plate.count
                plate.count -= used_count
                # Добавляем плиту в конфигурацию столько раз, сколько использовано
                current_config.plates.extend([plate] * used_count)

            # Расчет стоимости для использованных плит
            concrete_price = next(
                (cc.price for cc in prices.concrete_classes if cc.name == current_config.concrete_class), 0
            )
            cost = 0
            for plate in current_config.plates:
                cost += current_config.wire_bottom * prices.wire.price
                cost += current_config.wire_top * prices.wire.price
                cost += (
                                    plate.length / 1000 * current_config.height / 1000 * current_config.width / 1000) * concrete_price
            current_config.total_cost = cost

            # Аналогично считаем стоимость неиспользуемого объёма
            free_cost = ((current_config.free_len / 1000 * current_config.height / 1000 * current_config.width / 1000)
                         * concrete_price)
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
