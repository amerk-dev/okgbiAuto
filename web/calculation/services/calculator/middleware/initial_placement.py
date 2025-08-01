"""
Initial placement middleware for the calculator module.
"""
import datetime
from collections import defaultdict
from ..utils import add_plate_to_track
from .base import Middleware, MiddlewareContext


class InitialPlacementMiddleware(Middleware):
    """Слой 1: Распределение по размерам."""

    def _group_plates(self, plates, include_deadline=True):
        groups = defaultdict(list)
        for plate in plates:
            key = (
                plate.deadline.date if include_deadline and hasattr(plate, 'deadline') and plate.deadline.date else datetime.date.max,
                plate.width, plate.height,
                plate.concrete_class, plate.wire_bottom, plate.wire_top
            )
            groups[key].append(plate)
        return groups

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        print("Запуск InitialPlacementMiddleware...")
        plate_groups = self._group_plates(context.plates)
        ready_plate_groups = self._group_plates(context.ready_plates, include_deadline=False)

        # Слой 1: Распределение по размерам
        for track in context.tracks:
            if track.customer:
                print(f"Дорожка {track} зарезервирована под заказчика")
                continue
            remaining_length = context.track_len
            current_track_properties = None

            # Проверяем готовые плиты
            for group_key, group_plates in sorted(ready_plate_groups.items(), key=lambda x: x[0][0]):
                group_plates = [p for p in group_plates if p.id not in context.placed_plate_ids]
                if not group_plates:
                    continue
                plate = group_plates[0]
                plate_properties = (plate.width, plate.height)
                if current_track_properties and plate_properties != current_track_properties:
                    continue
                if not current_track_properties:
                    current_track_properties = plate_properties
                group_plates.sort(key=lambda p: p.length, reverse=True)
                for plate in group_plates:
                    if plate.length <= remaining_length:
                        add_plate_to_track(plate, track)
                        context.placed_plate_ids.add(plate.id)
                        remaining_length -= plate.length
                        context.plan.append((track, plate, "ready"))

            # Распределяем новые плиты
            for group_key, group_plates in sorted(plate_groups.items(), key=lambda x: x[0][0]):
                group_plates = [p for p in group_plates if p.id not in context.placed_plate_ids]
                if not group_plates:
                    continue
                plate = group_plates[0]
                plate_properties = (plate.width, plate.height)
                if current_track_properties and plate_properties != current_track_properties:
                    continue
                if not current_track_properties:
                    current_track_properties = plate_properties
                group_plates.sort(key=lambda p: p.length, reverse=True)
                for plate in group_plates:
                    if plate.length <= remaining_length:
                        add_plate_to_track(plate, track)
                        context.placed_plate_ids.add(plate.id)
                        remaining_length -= plate.length
                        context.plan.append((track, plate, "new"))
        print("InitialPlacementMiddleware завершен.")
        return context