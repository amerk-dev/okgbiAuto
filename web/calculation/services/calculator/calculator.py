"""
Main calculator class for the calculator module.
"""
from calculation.models import Track, ReadyPlate, Plate
from .middleware import (
    MiddlewareContext,
    InitialPlacementMiddleware,
    ConcreteClassOptimizationMiddleware,
    WireOptimizationMiddleware,
)
from .utils import profile_time, get_parameters, reality_check


class PlanCalculator:
    """Class for calculating the plan using middleware chain."""

    def __init__(self):
        """Initialize the calculator with default middlewares."""
        self.middlewares = [
            InitialPlacementMiddleware(),
            ConcreteClassOptimizationMiddleware(),
            WireOptimizationMiddleware(),
        ]

    @profile_time
    def calculate_plan(self):
        """Main method to calculate the plan using middleware chain."""
        track_len, tail_len = get_parameters()
        tracks = Track.get_tracks()  # Предполагаем, что это метод модели
        ready_plates = ReadyPlate.objects.all()
        plates = Plate.objects.filter(track__isnull=True)

        # ToDo Распределить какие готовые плиты можно использовать
        if ready_plates.exists():
            print(f"Найдено {ready_plates.count()} готовых плит.")
        else:
            print("Готовых плит нет.")

        if not plates.exists() and not ready_plates.exists():
            print("Нет плит для размещения. План пуст.")
            return {"plan": [], "Use_ready_plates": 0, "is_real": True}

        is_real = reality_check(plates, tracks, track_len)

        # Инициализация контекста
        context = MiddlewareContext(
            tracks=tracks,
            track_len=track_len,
            plates=plates,
            ready_plates=ready_plates
        )

        # Выполнение цепочки middleware
        for middleware in self.middlewares:
            context = middleware.process(context)

        # Формирование финального результата
        context.unplaced_plates = [p for p in plates if p.id not in context.placed_plate_ids]
        if context.unplaced_plates:
            print(f"{len(context.unplaced_plates)} новых плит не удалось разместить: {[str(p) for p in context.unplaced_plates]}")

        # Также проверим неразмещенные готовые плиты (если это нужно)
        unplaced_ready_plates = [p for p in ready_plates if p.id not in context.placed_plate_ids]
        if unplaced_ready_plates:
            print(f"{len(unplaced_ready_plates)} готовых плит не удалось разместить: {[str(p) for p in unplaced_ready_plates]}")

        result = {
            "plan": [(str(t), str(p), s) for t, p, s in context.plan],
            "Use_ready_plates": len([p for _, p, s in context.plan if s == "ready"]),
            "is_real": is_real,
            "unplaced_plates_count": len(context.unplaced_plates)
        }

        print("Финальный план:")
        print(result)
        return result

    def add_middleware(self, middleware):
        """Add a middleware to the chain."""
        self.middlewares.append(middleware)
        return self

    def set_middlewares(self, middlewares):
        """Set the middleware chain."""
        self.middlewares = middlewares
        return self