import datetime
import time
from collections import defaultdict
from itertools import combinations
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
    track_len, tail_len = get_parameters()

    tracks = Track.get_tracks()
    orders = Order.objects.all()
    ready_plates = ReadyPlate.objects.all()
    # ToDo Распределить какие готовые плиты можно использовать
    if ready_plates:
        pass
    else:
        print("Готовых плит нет.")
    plates = Plate.objects.filter(track__isnull=True)
    is_real = reality_check(plates, tracks, track_len)
    plan = create_plan(tracks, track_len)
    print({f"plan": plan,
           "Use_ready_plates": 0, # Плиты со склада, которые подходят под заказ
           "is_real": is_real}
          )


@profile_time
def create_plan(tracks, track_len):
    """Основная функция - алгоритм распределения плит по дорожкам
    Args:
        tracks (list[Track]): Список доступных дорожек.
        track_len (int): Максимальная длина каждой дорожки.
        plates (Plate): Список плит, которые нужно разместить.
    """

    plates = Plate.objects.filter(track__isnull=True).select_related('deadline')
    ready_plates = ReadyPlate.objects.all()
    if not plates and not ready_plates:
        print("Нет плит для размещения. План пуст.")
        return []

    # Группировка плит по свойствам
    def group_plates(plates, include_deadline=True):
        groups = defaultdict(list)
        for plate in plates:
            key = (
                plate.deadline.date if include_deadline and hasattr(plate,
                                                                    'deadline') and plate.deadline.date else datetime.date.max,
                plate.width, plate.height,
                plate.concrete_class, plate.wire_bottom, plate.wire_top
            )
            groups[key].append(plate)
        return groups

    plate_groups = group_plates(plates)
    ready_plate_groups = group_plates(ready_plates, include_deadline=False)

    placed_plate_ids = set()
    plan = []

    # Слой 1: Распределение по размерам
    for track in tracks:
        if track.customer:
            print(f"Дорожка {track} зарезервирована под заказчика")
            continue

        remaining_length = track_len
        current_track_properties = None

        # Проверяем готовые плиты
        for group_key, group_plates in sorted(ready_plate_groups.items(), key=lambda x: x[0][0]):
            group_plates = [p for p in group_plates if p.id not in placed_plate_ids]
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
                    placed_plate_ids.add(plate.id)
                    remaining_length -= plate.length
                    plan.append((track, plate, "ready"))

        # Распределяем новые плиты
        for group_key, group_plates in sorted(plate_groups.items(), key=lambda x: x[0][0]):
            group_plates = [p for p in group_plates if p.id not in placed_plate_ids]
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
                    placed_plate_ids.add(plate.id)
                    remaining_length -= plate.length
                    plan.append((track, plate, "new"))

    # Слой 2: Оптимизация по классу бетона
    for track in tracks:
        track_plates = [p for t, p, _ in plan if t == track]
        if not track_plates:
            continue

        # Группируем плиты на дорожке по concrete_class
        concrete_groups = defaultdict(list)
        for plate in track_plates:
            concrete_groups[plate.concrete_class].append(plate)

        if len(concrete_groups) > 1:
            # Проверяем возможность обмена с другими дорожками
            for other_track in tracks:
                if other_track == track or other_track.customer:
                    continue
                other_plates = [p for t, p, _ in plan if t == other_track]
                if not other_plates:
                    continue

                other_concrete_groups = defaultdict(list)
                for plate in other_plates:
                    other_concrete_groups[plate.concrete_class].append(plate)

                # Проверяем, можно ли обменять плиты с одинаковыми размерами
                for plate1, plate2 in combinations(track_plates + other_plates, 2):
                    if (plate1.id not in placed_plate_ids or plate2.id not in placed_plate_ids or
                            plate1.width != plate2.width or plate1.height != plate2.height):
                        continue

                    # Проверяем, уменьшит ли обмен количество уникальных concrete_class
                    track_cost_before = track.cost
                    other_track_cost_before = other_track.cost
                    swap_plates(plate1, plate2, track, other_track)
                    if track.cost + other_track.cost < track_cost_before + other_track_cost_before:
                        plan = [(t, p, s) if (t, p, s) != (track, plate1, "new") and (t, p, s) != (other_track, plate2,
                                                                                                   "new")
                                else (other_track, plate1, "new") if p == plate2 else (track, plate2, "new")
                                for t, p, s in plan]
                    else:
                        swap_plates(plate1, plate2, other_track, track)  # Откат

    # Слой 3: Оптимизация по проволоке
    for track in tracks:
        track_plates = [p for t, p, _ in plan if t == track]
        if not track_plates:
            continue

        wire_groups = defaultdict(list)
        for plate in track_plates:
            wire_groups[(plate.wire_bottom, plate.wire_top)].append(plate)

        if len(wire_groups) > 1:
            for other_track in tracks:
                if other_track == track or other_track.customer:
                    continue
                other_plates = [p for t, p, _ in plan if t == other_track]
                if not other_plates:
                    continue

                for plate1, plate2 in combinations(track_plates + other_plates, 2):
                    if (plate1.id not in placed_plate_ids or plate2.id not in placed_plate_ids or
                            plate1.width != plate2.width or plate1.height != plate2.height or
                            plate1.concrete_class != plate2.concrete_class):
                        continue

                    track_cost_before = track.cost
                    other_track_cost_before = other_track.cost
                    swap_plates(plate1, plate2, track, other_track)
                    if track.cost + other_track.cost < track_cost_before + other_track_cost_before:
                        plan = [(t, p, s) if (t, p, s) != (track, plate1, "new") and (t, p, s) != (other_track, plate2,
                                                                                                   "new")
                                else (other_track, plate1, "new") if p == plate2 else (track, plate2, "new")
                                for t, p, s in plan]
                    else:
                        swap_plates(plate1, plate2, other_track, track)

    # Вывод результатов
    unplaced_plates = [p for p in plates if p.id not in placed_plate_ids]
    if unplaced_plates:
        print(f"{len(unplaced_plates)} плит не удалось разместить: {[str(p) for p in unplaced_plates]}")

    # Формируем результат
    result = {
        "plan": [(str(t), str(p), s) for t, p, s in plan],
        "Use_ready_plates": len([p for _, p, s in plan if s == "ready"]),
        "is_real": reality_check(plates, tracks, track_len)
    }
    print(result)
    return result


def swap_plates(plate1, plate2, track1, track2):
    """Меняет плиты между дорожками."""
    plate1.track = track2
    plate2.track = track1
    plate1.save()
    plate2.save()



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


def add_plate_to_track(plate, track):
    plate.track = track
    try:
        plate.save()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении плиты {plate} на дорожку {track}: {e}")
        return False
