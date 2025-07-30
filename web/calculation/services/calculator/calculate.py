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


    print(track_len , tail_len)
    tracks = Track.get_tracks()
    orders = Order.objects.all()
    ready_plates = ReadyPlate.objects.all()

    plates = Plate.objects.filter(track__isnull=True)



@profile_time
def reality_check():
    pass