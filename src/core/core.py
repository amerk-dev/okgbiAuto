from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import models


def calculate_plan(spec: models.ProductionSpecification):
    available_tracks = spec.available_tracks
    track_len = spec.directory.track.length
    print(available_tracks, track_len)
    orders = spec.orders
    ready_plates = spec.ready_plates  # Плиты которые уже изгоотвлены
    need_create_plates, ready_plates = hasReadyPlate(orders, ready_plates)  # Плиты которые надо изготовить
    # print(
    #     "need_create_plates -", need_create_plates,
    #     "\nОстаток готовых плит", ready_plates
    # )

    # for track in available_tracks:
    #     if track.count > 0:
    #         print(track.day)
    # Укладываем плиты на дорожку
    print(need_create_plates)
    res = bestPlates(available_tracks, track_len, need_create_plates, spec.directory)

    return res


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
    print(prices)
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
        # Уменьшаем количество доступных треков
        tracks.count -= 1

    return tracks_config


def calculate_optimal_for_track_plan(spec: models.ProductionSpecification) -> Dict:
    # Преобразование доступных дорожек в словарь {дата: количество}
    available_tracks = {track.day: track.count for track in spec.available_tracks}

    # Сбор всех плит с привязкой к дате и заказу
    date_order_plates = defaultdict(lambda: defaultdict(list))
    for order in spec.orders:
        for completion in order.completion_dates:
            date_obj = completion.date  # Уже datetime.date, не нужно преобразовывать
            for plate in completion.plates:
                # Умножаем плиты по количеству
                for _ in range(plate.count):
                    date_order_plates[date_obj][order.number].append(plate)

    result_days = []

    # Обработка для каждой даты
    for date, orders in date_order_plates.items():
        # Получаем доступное количество дорожек для этой даты
        max_tracks = available_tracks.get(date, 0)
        if max_tracks == 0:
            continue

        # Собираем все плиты для даты
        all_plates = [plate for order_plates in orders.values() for plate in order_plates]

        # Группировка плит по характеристикам
        size_groups = defaultdict(list)
        for plate in all_plates:
            key = (
                plate.width,
                plate.height,
                plate.concrete_class,
                plate.wire_top,
                plate.wire_bottom
            )
            size_groups[key].append(plate)

        # Расчет параметров для каждой группы
        group_data = []
        concrete_class_map = {c.name: c.price for c in spec.directory.concrete_classes}
        for key, plates in size_groups.items():
            total_length = sum(p.length for p in plates)
            volume = sum(p.length * p.width * p.height for p in plates) / 1e9  # m³
            concrete_cost = volume * concrete_class_map[key[2]]
            wire_cost = sum((p.wire_top + p.wire_bottom) * spec.directory.wire.price for p in plates)

            group_data.append({
                "key": key,
                "plates": plates,
                "total_length": total_length,
                "cost": concrete_cost + wire_cost + spec.directory.retooling.price,
                "efficiency": (concrete_cost + wire_cost) / total_length  # Стоимость на мм
            })

        # Сортировка групп по эффективности (наиболее выгодные сначала)
        sorted_groups = sorted(group_data, key=lambda x: -x["efficiency"])

        # Распределение по дорожкам
        tracks = []
        current_track = {
            "groups": [],
            "used_length": 0,
            "total_cost": 0.0
        }

        for group in sorted_groups:
            placed = False
            # Пытаемся добавить в существующие дорожки
            for track in tracks:
                if track["used_length"] + group["total_length"] <= 85000:
                    track["groups"].append(group)
                    track["used_length"] += group["total_length"]
                    track["total_cost"] += group["cost"]
                    placed = True
                    break

            # Создаем новую дорожку если есть возможность
            if not placed and len(tracks) < max_tracks:
                tracks.append({
                    "groups": [group],
                    "used_length": group["total_length"],
                    "total_cost": group["cost"]
                })

        # Формирование результата для даты
        day_entry = {
            "date": date.strftime("%Y-%m-%d"),  # Преобразуем дату в строку для вывода
            "tracks": []
        }

        for track in tracks:
            # Собираем все плиты в дорожке
            track_plates = [plate for group in track["groups"] for plate in group["plates"]]

            # Группировка по заказам
            order_map = defaultdict(list)
            for plate in track_plates:
                order_num = next(
                    num for num, plates in orders.items()
                    if plate in plates
                )
                order_map[order_num].append(plate)

            # Формирование структуры заказов
            formatted_orders = []
            for order_num, plates in order_map.items():
                order_plates = []
                for plate in plates:
                    volume = (plate.length * plate.width * plate.height) / 1e9
                    concrete_cost = volume * concrete_class_map[plate.concrete_class]
                    wire_cost = (plate.wire_top + plate.wire_bottom) * spec.directory.wire.price

                    order_plates.append({
                        "count": 1,
                        "length": plate.length,
                        "production_plate": {
                            "material_cost": round(concrete_cost + wire_cost, 2)
                        },
                        "order_plate": {
                            "material_cost": round(concrete_cost + wire_cost, 2),
                            "concrete_class": plate.concrete_class,
                            "wire_top": plate.wire_top,
                            "wire_bottom": plate.wire_bottom
                        }
                    })

                formatted_orders.append({
                    "number": order_num,
                    "plates": order_plates
                })

            # Параметры первой группы в дорожке
            first_group = track["groups"][0]["key"]

            day_entry["tracks"].append({
                "width": first_group[0],
                "height": first_group[1],
                "concrete_class": first_group[2],
                "wire_top": first_group[3],
                "wire_bottom": first_group[4],
                "total_cost": round(track["total_cost"], 2),
                "useful_length": track["used_length"],
                "useful_cost": round(track["total_cost"] - spec.directory.retooling.price * len(track["groups"]), 2),
                "free_length": 85000 - track["used_length"],
                "free_cost": 0.0,
                "orders": formatted_orders
            })

        result_days.append(day_entry)

    return {"days": result_days}


def calculate_optimal_cost_plan(spec: models.ProductionSpecification) -> Dict:
    # Инициализация параметров
    concrete_prices = {c.name: c.price for c in spec.directory.concrete_classes}
    wire_price = spec.directory.wire.price
    retooling_price = spec.directory.retooling.price
    track_length = 85000
    available_tracks = {t.day: t.count for t in spec.available_tracks}

    # Сбор всех плит с информацией о крайнем сроке
    all_plates = []
    for order in spec.orders:
        for completion in order.completion_dates:
            deadline = completion.date
            for plate in completion.plates:
                for _ in range(plate.count):
                    all_plates.append({
                        "plate": plate,
                        "deadline": deadline
                    })

    # Группировка плит по характеристикам (без учета даты)
    groups = defaultdict(list)
    for item in all_plates:
        plate = item["plate"]
        key = (
            plate.concrete_class,
            plate.wire_top,
            plate.wire_bottom,
            plate.width,
            plate.height
        )
        groups[key].append(item)

    # Оптимизированное распределение
    tracks = []
    for group_key, items in groups.items():
        # Определяем самый поздний допустимый день производства
        deadlines = [item["deadline"] for item in items]
        max_deadline = max(deadlines)

        # Разбиваем на части по 85 метров
        total_length = sum(item["plate"].length for item in items)
        num_tracks_needed = (total_length + track_length - 1) // track_length

        # Распределяем по дням до дедлайна
        production_day = find_optimal_day(
            max_deadline,
            num_tracks_needed,
            available_tracks
        )

        if production_day:
            tracks.append({
                "key": group_key,
                "day": production_day,
                "count": num_tracks_needed,
                "items": items
            })
            available_tracks[production_day] -= num_tracks_needed

    # Формирование результата с группировкой по дням
    result_days = defaultdict(list)
    for track in tracks:
        # Расчет стоимости
        total_concrete = sum(
            (p["plate"].length * p["plate"].width * p["plate"].height) / 1e9 *
            concrete_prices[track["key"][0]]
            for p in track["items"]
        )

        total_wire = sum(
            (p["plate"].wire_top + p["plate"].wire_bottom) * wire_price
            for p in track["items"]
        )

        # Формирование записи дорожки
        track_entry = {
            "width": track["key"][3],
            "height": track["key"][4],
            "concrete_class": track["key"][0],
            "wire_top": track["key"][1],
            "wire_bottom": track["key"][2],
            "total_cost": round(total_concrete + total_wire + retooling_price, 2),
            "useful_length": sum(p["plate"].length for p in track["items"]),
            "orders": []
        }

        # Группировка по заказам
        order_map = defaultdict(list)
        for item in track["items"]:
            order_num = next(
                o.number for o in spec.orders
                if any(cd.date == item["deadline"]
                       and item["plate"] in cd.plates
                       for cd in o.completion_dates)
            )
            order_map[order_num].append(item["plate"])

        # Формирование заказов
        for order_num, plates in order_map.items():
            order_entry = {
                "number": order_num,
                "plates": []
            }
            for plate in plates:
                volume = (plate.length * plate.width * plate.height) / 1e9
                order_entry["plates"].append({
                    "count": 1,
                    "length": plate.length,
                    "production_plate": {
                        "material_cost": round(volume * concrete_prices[plate.concrete_class] +
                                               (plate.wire_top + plate.wire_bottom) * wire_price, 2)
                    },
                    "order_plate": {
                        "material_cost": round(volume * concrete_prices[plate.concrete_class] +
                                               (plate.wire_top + plate.wire_bottom) * wire_price, 2),
                        "concrete_class": plate.concrete_class,
                        "wire_top": plate.wire_top,
                        "wire_bottom": plate.wire_bottom
                    }
                })
            track_entry["orders"].append(order_entry)

        result_days[track["day"].strftime("%Y-%m-%d")].append(track_entry)

    return {"days": [{"date": k, "tracks": v} for k, v in result_days.items()]}


def find_optimal_day(deadline: datetime.date,
                     needed_tracks: int,
                     available: Dict[datetime.date, int]) -> datetime.date:
    # Ищем последний возможный день с достаточным количеством дорожек
    for day in reversed([d for d in available.keys() if d <= deadline]):
        if available[day] >= needed_tracks:
            return day
    return None
