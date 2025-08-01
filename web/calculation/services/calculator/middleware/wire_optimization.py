"""
Wire optimization middleware for the calculator module.
"""
from collections import defaultdict
from ..utils import swap_plates
from .base import Middleware, MiddlewareContext


class WireOptimizationMiddleware(Middleware):
    """Слой 3: Оптимизация по проволоке."""

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        print("Запуск WireOptimizationMiddleware...")

        # Слой 3: Оптимизация по проволоке
        for track in context.tracks:
            track_plates = [p for t, p, _ in context.plan if t == track]
            if not track_plates:
                continue

            wire_groups = defaultdict(list)
            for plate in track_plates:
                wire_groups[(plate.wire_bottom, plate.wire_top)].append(plate)

            if len(wire_groups) > 1:
                for other_track in context.tracks:
                    if other_track == track or other_track.customer:
                        continue
                    other_plates = [p for t, p, _ in context.plan if t == other_track]
                    if not other_plates:
                        continue

                    # combinations из track_plates + other_plates может быть очень большим
                    # Ограничиваем перебор только плитами из текущих дорожек
                    for plate1 in track_plates:
                        for plate2 in other_plates:
                            if (plate1.id not in context.placed_plate_ids or plate2.id not in context.placed_plate_ids or
                                    plate1.width != plate2.width or plate1.height != plate2.height or
                                    plate1.concrete_class != plate2.concrete_class):
                                continue

                            # Более простая метрика: общее количество уникальных типов проволоки на двух дорожках
                            unique_before_track = len(set((p.wire_bottom, p.wire_top) for p in track_plates))
                            unique_before_other = len(set((p.wire_bottom, p.wire_top) for p in other_plates))
                            cost_before = unique_before_track + unique_before_other

                            # Симуляция обмена
                            plate1.track, plate2.track = plate2.track, plate1.track
                            # Пересчитываем плиты после симуляции
                            new_track_plates = [p for p in track_plates if p.id != plate1.id] + [plate2]
                            new_other_plates = [p for p in other_plates if p.id != plate2.id] + [plate1]
                            unique_after_track = len(set((p.wire_bottom, p.wire_top) for p in new_track_plates))
                            unique_after_other = len(set((p.wire_bottom, p.wire_top) for p in new_other_plates))
                            cost_after = unique_after_track + unique_after_other

                            if cost_after < cost_before:
                                print(f"Обмен плит {plate1.id} и {plate2.id} между дорожками {track.id} и {other_track.id} (по проволоке)")
                                # Фиксируем обмен в плане (упрощенная логика)
                                context.plan = [
                                    (other_track if t == track and p.id == plate1.id else
                                     track if t == other_track and p.id == plate2.id else t,
                                     plate2 if t == track and p.id == plate1.id else
                                     plate1 if t == other_track and p.id == plate2.id else p,
                                     source)
                                    for t, p, source in context.plan
                                ]
                                # Сохраняем изменения в БД
                                swap_plates(plate1, plate2, track, other_track)
                            else:
                                # Откат симуляции
                                plate1.track, plate2.track = plate2.track, plate1.track
        print("WireOptimizationMiddleware завершен.")
        return context