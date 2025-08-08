import datetime
import time
from collections import defaultdict
from typing import Any, List
from django.db.models import Min, Max

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

    Track().recreate_tracks()
    tracks = Track.get_tracks()

    ready_plates = ReadyPlate.objects.all()
    use_ready_plates = 0
    # Сравниваем нужные плиты и готовые, если в списке нужных плит есть плита равная готовой, то удаляем ее из бд
    for plate in ready_plates:
        need_plate = Plate.objects.filter(width=plate.width, height=plate.height,
                                          length=plate.length, concrete_class=plate.concrete_class,
                                          wire_bottom=plate.wire_bottom, wire_top=plate.wire_top).first()
        if need_plate:
            need_plate.delete()
            use_ready_plates+=1


    if not ready_plates:
        print("Готовых плит нет.")

    plates = Plate.objects.filter(track__isnull=True)
    is_real = reality_check(plates, tracks, track_len)
    plan = create_plan(tracks)
    print({f"plan": plan,
           "Use_ready_plates": use_ready_plates,  # Плиты со склада, которые подходят под заказ
           "is_real": is_real}
          )


@profile_time
def create_plan(tracks):
    """Основная функция - алгоритм распределения плит по дорожкам
    Args:
        tracks (list[Track]): Список доступных дорожек.
    """

    plates = Plate.objects.filter(track__isnull=True)
    track_len, tail_len = get_parameters()

    # Разделяем плиты на две группы
    plates_with_deadline = [p for p in plates if p.deadline.date is not None]
    plates_without_deadline = [p for p in plates if p.deadline.date is None]

    # Сортируем каждую группу
    plates_with_deadline.sort(key=lambda p: (p.deadline.date, p.width, p.height))
    plates_without_deadline.sort(key=lambda p: (p.width, p.height))

    if not plates_with_deadline and not plates_without_deadline:
        print("Нет плит для размещения. План пуст.")


    placed_plate_ids = set()

    # Функция для попытки размещения плит на дорожках
    def place_plates(plates_list, is_dedline = False):
        nonlocal placed_plate_ids
        prev_current_properties = None
        last_track_day = None
        for track in tracks:
            if last_track_day != track.day:
                prev_current_properties = None
            if track.customer:
                print("Дорожка зарезервирована под заказчика")
                continue

            remaining_length = track.free_length
            if prev_current_properties is not None and not is_dedline:
                current_track_properties = prev_current_properties
            elif track.width is not None and track.height is not None:
                current_track_properties = (track.width, track.height)
            else:
                current_track_properties = None

            current_track_properties = fill_track(plates_list, placed_plate_ids, remaining_length, track, current_track_properties)

            if track.free_length == track_len:
                current_track_properties = None
                current_track_properties = fill_track(plates_list, placed_plate_ids, remaining_length, track, current_track_properties)

            last_track_day = track.day
            prev_current_properties = current_track_properties
    # 1. Сначала размещаем плиты с дедлайнами
    place_plates(plates_with_deadline, True)
    # 2. Затем — без дедлайнов
    place_plates(plates_without_deadline)

    # Плиты, которые не удалось разместить
    unplaced_plates = [p for p in plates if p.id not in placed_plate_ids]
    if unplaced_plates:
        print(f"{len(unplaced_plates)} плит не удалось разместить.")

    post_calculating()
    # # post_calculating()
    return True

@profile_time
def fill_track(plates_list, placed_plate_ids, remaining_length, track, current_track_properties):
    for plate in plates_list:
        if plate.id in placed_plate_ids:
            continue

        plate_properties = (plate.width, plate.height)

        if current_track_properties is None and plate.length <= remaining_length:
            current_track_properties = plate_properties
            remaining_length -= plate.length
            add_plate_to_track(plate, track)
            placed_plate_ids.add(plate.id)
        elif plate_properties == current_track_properties and plate.length <= remaining_length:
            remaining_length -= plate.length
            add_plate_to_track(plate, track)
            placed_plate_ids.add(plate.id)
        track.save()
    return current_track_properties

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


@profile_time
def post_calculating():
    # Собрать все дорожки с плитами
    tracks_with_plates = Track.objects.filter(plates__isnull=False).distinct()
    tasks = []
    for track in tracks_with_plates:
        plates = list(track.plates.all())
        if not plates:
            continue
        width = plates[0].width
        height = plates[0].height
        min_deadline = min(plate.deadline.date for plate in plates if plate.deadline.date is not None) if any(
            plate.deadline.date is not None for plate in plates) else None
        tasks.append({
            'plates': plates,
            'width': width,
            'height': height,
            'min_deadline': min_deadline
        })

    # Получить все дорожки как позиции, упорядоченные по дню и позиции
    all_tracks = Track.objects.all().order_by('day', 'position')

    # Очистить все назначения
    Plate.objects.all().update(track=None)

    available_tasks = tasks.copy()
    previous_properties = None
    for position_track in all_tracks:
        day = position_track.day
        # Фильтровать задания, которые можно разместить
        candidates = [task for task in available_tasks if task['min_deadline'] is None or task['min_deadline'] >= day]
        if not candidates:
            continue
        # Предпочесть задание с таким же (ширина, высота), как предыдущее
        if previous_properties:
            matching = [task for task in candidates if (task['width'], task['height']) == previous_properties]
            chosen_task = matching[0] if matching else candidates[0]
        else:
            chosen_task = candidates[0]
        # Назначить плиты на дорожку
        for plate in chosen_task['plates']:
            plate.track = position_track
            plate.save()
        previous_properties = (chosen_task['width'], chosen_task['height'])
        available_tasks.remove(chosen_task)

    if available_tasks:
        print(f"Не удалось разместить {len(available_tasks)} заданий")


@profile_time
def swap_track_to_end(tracks, this_track):
    for track in tracks:
        if this_track.id != track.id:
            track.id, this_track.id = this_track.id, track.id
    return True


@profile_time
def swap_track_to_deadline(tracks: List[Track], this_track, day):
    # Берем айдишники и меняем всю инфу местами, если у предыдущего нет ограничений
    for track in tracks:
        if track.day >= day:
            break
        if track.day < day and track.id != this_track.id:
            track.id, this_track.id = this_track.id, track.id
    return True


@profile_time
def swap_to_one():
    tracks = list(Track.get_tracks())  # Step 1: Convert to list
    max_tail_len = Parameters.get_solo().tail_length

    updated_tracks = []
    deadlines = {}
    for track in tracks:
        agg = Plate.objects.filter(track=track.id).aggregate(
            min_date=Min('deadline__date'),
            max_date=Max('deadline__date')
        )
        deadlines[track.id] = {
            'min': agg['min_date'],
            'max': agg['max_date']
        }

    # Iterate over tracks starting from index 1
    for i in range(1, len(tracks)):
        track = tracks[i]
        if track.customer:
            continue
        if track.free_length > max_tail_len:
            min_deadline_i = deadlines.get(track.id, {}).get('min')
            max_deadline_i = deadlines.get(track.id, {}).get('max')
            if min_deadline_i is None or max_deadline_i is None:
                continue
            # Check if sizes differ from the previous track
            if tracks[i - 1].width != track.width or tracks[i - 1].height != track.height:
                # Look for a suitable track to swap with
                for j in range(i + 1, len(tracks)):
                    if tracks[j].day > max_deadline_i:
                        break
                    if (tracks[j].width == tracks[i - 1].width and
                            tracks[j].height == tracks[i - 1].height):
                        min_deadline_j = deadlines.get(tracks[j].id, {}).get('min')
                        if (min_deadline_j is not None and
                                tracks[j].day <= min_deadline_i and
                                tracks[i].day <= min_deadline_j):
                            # Perform the swap (Step 2: Swap elements)
                            tracks[i], tracks[j] = tracks[j], tracks[i]
                            updated_tracks.append(tracks[i])
                            updated_tracks.append(tracks[j])
                            break

        # Шаг 3: Обновляем позиции внутри каждого дня на основе порядка в списке
        day_track_indices = defaultdict(list)
        for idx, track in enumerate(tracks):
            day_track_indices[track.day].append((idx, track))

        for day, idx_tracks in day_track_indices.items():
            # Сортируем дорожки внутри дня по их порядку в списке
            sorted_tracks = [track for _, track in sorted(idx_tracks, key=lambda x: x[0])]
            for pos, track in enumerate(sorted_tracks):
                track.position = pos

    # Update the database with the new positions
    if updated_tracks or tracks:
        Track.objects.bulk_update(tracks, ['position', 'day'])