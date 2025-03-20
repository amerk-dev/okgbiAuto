from typing import Dict, List
import models

def calculate_plan(spec: models.ProductionSpecification) -> Dict:
    plates = [
        plate
        for order in spec.orders
        for completion_date in order.completion_dates
        for plate in completion_date.plates
    ]

    print(plates)

    # Группировка плит по рамерам
    plate_groups = {}
    for plate in plates:
        size_key = (plate.width, plate.height)
        key = f"{size_key}"
        if key not in plate_groups:
            plate_groups[key] = []
        plate_groups[key].append(plate.dict())

    return plate_groups