from typing import Dict, List
from collections import defaultdict
import datetime

import models


def calculate_plan(spec: models.ProductionSpecification) -> Dict:
    tracks = spec.available_tracks
    total_track_length = 85000  # Общая длина дорожки

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

    # Формирование итоговой структуры
    result_days = []

    for date, groups in days_dict.items():
        day_entry = {
            "date": date,
            "tracks": []
        }

        for size_group, plates_in_group in groups.items():
            # Рассчитываем общую длину для группы
            total_length = sum(p["plate"].length for p in plates_in_group)

            # Запись для дорожки
            track_entry = {
                "width": size_group[0],
                "height": size_group[1],
                "concrete_class": size_group[2],
                "wire_top": size_group[3],
                "wire_bottom": size_group[4],
                "total_cost": "",
                "useful_length": total_length,
                "useful_cost": "",
                "free_length": total_track_length - total_length,
                "free_cost": "",
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
                    plate_entry = {
                        "count": 1,  # Уже учтено через range(plate.count)
                        "length": plate.length,
                        "production_plate": {
                            "material_cost": ""
                        },
                        "order_plate": {
                            "material_cost": "",
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