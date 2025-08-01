"""
Utility functions for the calculator module.
"""
import time
from django.db import models
from calculation.models import Parameters


def profile_time(func):
    """Decorator to profile the execution time of a function."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result
    return wrapper


def get_parameters():
    """Получает и возвращает ключевые параметры для расчета плана."""
    params = Parameters.get_solo()
    # Предполагаем, что get_solo() возвращает объект с атрибутами
    return params.road_length, params.tail_length


def swap_plates(plate1, plate2, track1, track2):
    """Меняет плиты между дорожками."""
    plate1.track = track2
    plate2.track = track1
    plate1.save()
    plate2.save()


def reality_check(plates, tracks, track_len):
    """Проверка возможности размещения всех плит."""
    all_plates_len = 0
    all_track_len = 0
    for plate in plates:
        all_plates_len += plate.length
    for _ in tracks:
        all_track_len += track_len
    if all_track_len < all_plates_len:
        print("Не хватает длинны дорожек для выполнения заказов")
        return False
    else:
        print("Длинны дорожек хватает для выполнения заказов")
        return True


def add_plate_to_track(plate, track):
    """Добавляет плиту на дорожку."""
    plate.track = track
    try:
        plate.save()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении плиты {plate} на дорожку {track}: {e}")
        return False
