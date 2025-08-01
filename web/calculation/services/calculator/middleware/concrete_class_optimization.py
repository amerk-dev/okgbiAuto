"""
Concrete class optimization middleware for the calculator module.
"""
from collections import defaultdict
from ..utils import swap_plates
from .base import Middleware, MiddlewareContext


class ConcreteClassOptimizationMiddleware(Middleware):
    """Слой 2: Оптимизация по классу бетона."""

    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        print("Запуск ConcreteClassOptimizationMiddleware...")

        # Слой 2: Оптимизация по классу бетона
        for track in context.tracks:
            track_plates = [p for t, p, _ in context.plan if t == track]
            if not track_plates:
                continue

            # Группируем плиты на дорожке по concrete_class
            concrete_groups = defaultdict(list)
            for plate in track_plates:
                concrete_groups[plate.concrete_class].append(plate)

            if len(concrete_groups) > 1:
                # Проверяем возможность обмена с другими дорожками
                for other_track in context.tracks:
                    if other_track == track or other_track.customer:
                        continue
                    other_plates = [p for t, p, _ in context.plan if t == other_track]
                    if not other_plates:
                        continue
                    other_concrete_groups = defaultdict(list)
                    for plate in other_plates:
                        other_concrete_groups[plate.concrete_class].append(plate)

                    # Проверяем, можно ли обменять плиты с одинаковыми размерами
                    # combinations из track_plates + other_plates может быть очень большим
                    # Ограничиваем перебор только плитами из текущих дорожек
                    for plate1 in track_plates:
                        for plate2 in other_plates:
                            if (plate1.id not in context.placed_plate_ids or plate2.id not in context.placed_plate_ids or
                                    plate1.width != plate2.width or plate1.height != plate2.height):
                                continue

                            # Проверяем, уменьшит ли обмен количество уникальных concrete_class
                            # track.cost и other_track.cost - это свойства моделей?
                            # Предположим, что cost - это количество уникальных concrete_class на дорожке
                            # track_cost_before = track.cost
                            # other_track_cost_before = other_track.cost

                            # Более простая метрика: общее количество уникальных классов бетона на двух дорожках
                            unique_before_track = len(set(p.concrete_class for p in track_plates))
                            unique_before_other = len(set(p.concrete_class for p in other_plates))
                            cost_before = unique_before_track + unique_before_other

                            # Симуляция обмена
                            plate1.track, plate2.track = plate2.track, plate1.track
                            # Пересчитываем плиты после симуляции
                            new_track_plates = [p for p in track_plates if p.id != plate1.id] + [plate2]
                            new_other_plates = [p for p in other_plates if p.id != plate2.id] + [plate1]
                            unique_after_track = len(set(p.concrete_class for p in new_track_plates))
                            unique_after_other = len(set(p.concrete_class for p in new_other_plates))
                            cost_after = unique_after_track + unique_after_other

                            if cost_after < cost_before:
                                print(f"Обмен плит {plate1.id} и {plate2.id} между дорожками {track.id} и {other_track.id}")
                                # Фиксируем обмен в плане
                                # Это упрощенная логика обновления плана
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
        print("ConcreteClassOptimizationMiddleware завершен.")
        return context