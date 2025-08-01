"""
Base middleware classes for the calculator module.
"""
from typing import List, Tuple, Set
from calculation.models import Track, Plate


class MiddlewareContext:
    """Контекст для передачи данных между слоями."""
    def __init__(self, tracks, track_len, plates, ready_plates):
        self.tracks = tracks
        self.track_len = track_len
        self.plates = plates
        self.ready_plates = ready_plates
        self.plan: List[Tuple[Track, Plate, str]] = []  # (Track, Plate, source: "ready"/"new")
        self.placed_plate_ids: Set[int] = set()
        # Дополнительные данные, которые могут быть полезны
        self.unplaced_plates: List[Plate] = []


class Middleware:
    """Базовый класс для middleware."""
    def process(self, context: MiddlewareContext) -> MiddlewareContext:
        raise NotImplementedError