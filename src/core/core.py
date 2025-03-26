from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import models

def calculate_plan(spec: models.ProductionSpecification) -> Dict:
    tracks = spec.available_tracks
    total_track_length = 85000  # длина дорожки

    # Получаем цены
    concrete_price = {name[1]: price[1] for name, price in spec.directory.concrete_classes}
    wire_price = spec.directory.wire.price
    retooling_price = spec.directory.retooling.price


    # Собираем все плиты с привязкой к заказу и дате
    plates = []
    for order in spec.orders:
        for completion_date in order.completion_dates:
            for plate in completion_date.plates:
                for _ in range(plate.count):
                    plates.append({
                        "order_number": order.number,
                        "date": completion_date.date,
                        "plate": plate
                    })

    # Группировка по датам и характеристикам плит
    days_dict = defaultdict(lambda: defaultdict(list))

    for item in plates:
        plate = item["plate"]
        key = (
            plate.width,
            plate.height,
            plate.concrete_class,
            plate.wire_top,
            plate.wire_bottom
        )
        days_dict[item["date"]][key].append({
            "order_number": item["order_number"],
            "plate": plate
        })

    # Формирование итоговой структуры с расчетами
    result_days = []

    for date, groups in days_dict.items():
        day_entry = {
            "date": date,
            "tracks": []
        }

        for size_group, plates_in_group in groups.items():
            # Рассчитываем общую длину для группы
            total_length = sum(p["plate"].length for p in plates_in_group)
            # Расчет стоимости для всей группы
            concrete_cost = sum(
                (p["plate"].length * p["plate"].width * p["plate"].height) / 10**9 *  # мм³ → м³
                concrete_price[p["plate"].concrete_class]
                for p in plates_in_group
            )

            wire_cost = sum(
                (p["plate"].wire_top + p["plate"].wire_bottom) *
                wire_price
                for p in plates_in_group
            )

            retooling_cost = retooling_price  # Стоимость переналадки на группу

            # Запись для дорожки
            track_entry = {
                "width": size_group[0],
                "height": size_group[1],
                "concrete_class": size_group[2],
                "wire_top": size_group[3],
                "wire_bottom": size_group[4],
                "total_cost": round(concrete_cost + wire_cost + retooling_cost, 2),
                "useful_length": total_length,
                "useful_cost": round(concrete_cost + wire_cost, 2),
                "free_length": total_track_length - total_length,
                "free_cost": 0.0,  # Свободное место не генерирует затрат
                "orders": []
            }

            # Группируем плиты по заказам
            order_groups = defaultdict(list)
            for p in plates_in_group:
                order_groups[p["order_number"]].append(p["plate"])

            # Формируем записи заказов
            for order_number, order_plates in order_groups.items():
                order_entry = {
                    "number": order_number,
                    "plates": []
                }

                for plate in order_plates:
                    # Расчет стоимости для отдельной плиты
                    plate_volume = (plate.length * plate.width * plate.height) / 10**9
                    plate_concrete_cost = plate_volume * concrete_price[plate.concrete_class]
                    plate_wire_cost = (plate.wire_top + plate.wire_bottom) * wire_price

                    plate_entry = {
                        "count": 1,
                        "length": plate.length,
                        "production_plate": {
                            "material_cost": round(plate_concrete_cost + plate_wire_cost, 2)
                        },
                        "order_plate": {
                            "material_cost": round(plate_concrete_cost + plate_wire_cost, 2),
                            "concrete_class": plate.concrete_class,
                            "wire_top": plate.wire_top,
                            "wire_bottom": plate.wire_bottom
                        }
                    }
                    order_entry["plates"].append(plate_entry)

                track_entry["orders"].append(order_entry)

            day_entry["tracks"].append(track_entry)

        result_days.append(day_entry)

    return {"days": result_days}


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

    # Сбор и группировка всех плит по датам
    date_groups = defaultdict(lambda: defaultdict(list))
    for order in spec.orders:
        for completion in order.completion_dates:
            date = completion.date
            for plate in completion.plates:
                # Создаем ключ группировки по всем характеристикам
                group_key = (
                    plate.concrete_class,
                    plate.wire_top,
                    plate.wire_bottom,
                    plate.width,
                    plate.height
                )
                # Умножаем плиты по количеству
                date_groups[date][group_key].extend([plate] * plate.count)

    result_days = []

    # Обработка для каждой даты
    for date, groups in date_groups.items():
        max_tracks = available_tracks.get(date, 0)
        if max_tracks == 0:
            continue

        # Расчет стоимости для каждой группы
        group_data = []
        for key, plates in groups.items():
            total_len = sum(p.length for p in plates)
            volume = sum(p.length*p.width*p.height for p in plates)/1e9
            cost = (
                    volume * concrete_prices[key[0]] +
                    (key[1] + key[2]) * wire_price * len(plates)
            )
            group_data.append({
                "key": key,
                "length": total_len,
                "cost": cost,
                "plates": plates,
                "unit_cost": cost / total_len  # Стоимость за мм
            })

        # Сортировка по возрастанию стоимости за мм и убыванию длины
        sorted_groups = sorted(
            group_data,
            key=lambda x: (x["unit_cost"], -x["length"])
        )

        # Распределение по дорожкам
        tracks = []
        for group in sorted_groups:
            placed = False

            # Поиск подходящей дорожки
            for track in tracks:
                # Проверка совпадения характеристик и свободного места
                if (track["current_key"] == group["key"] and
                        track["remaining"] >= group["length"]):

                    track["groups"].append(group)
                    track["remaining"] -= group["length"]
                    track["total_cost"] += group["cost"]
                    placed = True
                    break

            # Если не найдено - создаем новую дорожку
            if not placed and len(tracks) < max_tracks:
                tracks.append({
                    "current_key": group["key"],
                    "groups": [group],
                    "remaining": track_length - group["length"],
                    "total_cost": group["cost"] + retooling_price
                })

        # Формирование результата
        day_result = {
            "date": date.strftime("%Y-%m-%d"),
            "tracks": []
        }

        for track in tracks:
            # Собираем все плиты
            all_plates = [p for g in track["groups"] for p in g["plates"]]

            # Группировка по заказам
            order_map = defaultdict(list)
            for plate in all_plates:
                order_num = next(
                    o.number for o in spec.orders
                    if any(cd.date == date and plate in cd.plates
                           for cd in o.completion_dates)
                )
                order_map[order_num].append(plate)

            # Параметры дорожки
            main_group = track["groups"][0]["key"]
            total_length = sum(g["length"] for g in track["groups"])

            track_entry = {
                "width": main_group[3],
                "height": main_group[4],
                "concrete_class": main_group[0],
                "wire_top": main_group[1],
                "wire_bottom": main_group[2],
                "total_cost": round(track["total_cost"], 2),
                "useful_length": total_length,
                "useful_cost": round(track["total_cost"] - retooling_price, 2),
                "free_length": track_length - total_length,
                "free_cost": 0.0,
                "orders": []
            }

            # Формирование заказов
            for order_num, plates in order_map.items():
                order_plates = []
                for plate in plates:
                    volume = (plate.length*plate.width*plate.height)/1e9
                    concrete_cost = volume * concrete_prices[plate.concrete_class]
                    wire_cost = (plate.wire_top + plate.wire_bottom) * wire_price

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

                track_entry["orders"].append({
                    "number": order_num,
                    "plates": order_plates
                })

            day_result["tracks"].append(track_entry)

        result_days.append(day_result)

    return {"days": result_days}