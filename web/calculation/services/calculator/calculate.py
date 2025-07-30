import datetime
import time
from typing import Any

from calculation.models import Track, Order, ReadyPlate, Plate, Parameters



def profile_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result

    return wrapper

# Классы для валидации и удобства разработки
class CustomTrack:
    id: int
    position: int
    len: int
    customer: int
    day: datetime.date

class Retooler:
    w: int
    h: int

def get_parameters():
    """Получает и возвращает ключевые параметры для расчета плана."""
    params = Parameters.get_solo()
    return {
        params.road_length,
        params.tail_length,
        # можно добавить и другие нужные параметры
    }

@profile_time
def calculate_plan():
    track_len, tail_len= get_parameters()

    tracks = Track.get_tracks()
    orders = Order.objects.all()
    ready_plates = ReadyPlate.objects.all()
    #ToDo Распределить какие готовые плиты можно использовать
    if ready_plates:
        pass
    else:
        print("Готовых плит нет.")
    plates = Plate.objects.filter(track__isnull=True)
    is_real = reality_check(plates, tracks, track_len)
    plan = create_plan()

@profile_time
def create_plan():
    pass



@profile_time
def reality_check(plates, tracks, track_len):
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

