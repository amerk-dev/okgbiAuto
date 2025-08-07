import datetime
import time
from typing import Any, List
from django.db.models import Min

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
    # ToDo Распределить какие готовые плиты можно
    # Сравниваем нужные плиты и готовые, если в списке нужных плит есть плита равная готовой, то удаляем ее из бд
    for plate in ready_plates:
        need_plate = Plate.objects.filter(width=plate.width, height=plate.height,
                                          length=plate.length, concrete_class=plate.concrete_class,
                                          wire_bottom=plate.wire_bottom, wire_top=plate.wire_top).first()
        if need_plate:
            need_plate.delete()
            print(plate)

    if ready_plates:
        pass
    else:
        print("Готовых плит нет.")
    plates = Plate.objects.filter(track__isnull=True)
    is_real = reality_check(plates, tracks, track_len)
    plan = create_plan(tracks, track_len)
    print({f"plan": plan,
           "Use_ready_plates": 0,  # Плиты со склада, которые подходят под заказ
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

    plates = Plate.objects.filter(track__isnull=True)
    # sort by date and (w:h)
    sorted_plates = sorted(
        [item for item in plates],
        key=lambda item: (
            # Если дата есть, используем ее. Если нет (None), используем максимальную возможную дату.
            item.deadline.date if item.deadline.date is not None else datetime.date.max,
            item.width,
            item.height
        )
    )
    if not sorted_plates:
        print("Нет плит для размещения. План пуст.")
        return []

    placed_plate_ids = set()

    # for i in sorted_plates:
    #     print(i.deadline.date, i)
    for track in tracks:
        if track.customer:
            print("Дорожка зарезервирована под заказчика")
            continue
        # ToDo Распределить новые плиты по дорожкам

        remaining_length = track_len
        current_track_properties = None

        for plate in sorted_plates:
            if plate.id in placed_plate_ids: continue

            plate_properties = (
                plate.width,
                plate.height
            )

            # Если это первая плита для данной дорожки (дорожка еще не настроена)
            if current_track_properties is None:
                current_track_properties = plate_properties

                # Размещаем плиту
                remaining_length -= plate.length
                add_plate_to_track(plate, track)
                placed_plate_ids.add(plate.id)
            elif plate_properties == current_track_properties:
                if plate.length <= remaining_length:
                    remaining_length -= plate.length
                    add_plate_to_track(plate, track)
                    placed_plate_ids.add(plate.id)

    unplaced_plates = [plate for plate in sorted_plates if plate.id not in placed_plate_ids]
    if unplaced_plates:
        print(f"{len(unplaced_plates)} плит не удалось разместить.")

        # if track.get_size is not None:
        #     add_plate_to_track(sorted_plates[0], track)
        #     sorted_plates.pop(0)
        # else:
        #     w, h = track.get_size
        #     need_plate_for_track = Plate.objects.filter(track=track).filter(
        #         deadline_date__isnull=True,
        #         track__isnull=True,
        #         width=w,
        #         height=h
        #     )
        #     print(track, need_plate_for_track)
    post_calculating()
    post_calculating()
    return True


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
    tracks = Track.get_tracks()
    max_tail_len = Parameters.get_solo().tail_length
    ft = Parameters.force_tail

    updated_tracks = []

    if ft == 0:
        for i in range(len(tracks) - 1):
            track = tracks[i]
            if track.customer:
                continue
            next_track = tracks[i + 1]
            if track.width != next_track.width or track.height != next_track.height:
                earliest_date = Plate.objects.filter(track=track.id).aggregate(
                    min_date=Min('deadline__date')
                )['min_date']
                if earliest_date is not None and track.free_length > max_tail_len:
                    swap_track_to_end(tracks, track)
                    updated_tracks.append(track)

    elif ft == 1:
        for track in tracks:
            if track.customer:
                continue
            earliest_date = Plate.objects.filter(track=track.id).aggregate(
                min_date=Min('deadline__date')
            )['min_date']
            if earliest_date is not None and track.free_length > max_tail_len:
                swap_track_to_end(tracks, track)
                updated_tracks.append(track)

    elif ft == 2:
        for track in tracks:
            # if had customers -> resume
            if track.customer:
                continue
            if track.free_length > max_tail_len:
                earliest_date = Plate.objects.filter(track=track.id).aggregate(
                    min_date=Min('deadline__date')
                )['min_date']
                if earliest_date is not None:
                    swap_track_to_deadline(tracks, track, earliest_date)
                else:
                    swap_track_to_end(tracks, track)
                updated_tracks.append(track)

    if updated_tracks:
        Track.objects.bulk_update(updated_tracks, ['position', 'day'])


@profile_time
def swap_track_to_end(tracks, this_track):
    for track in tracks:
        if this_track.id != track.id:
            track, this_track = this_track, track
    return True


@profile_time
def swap_track_to_deadline(tracks: List[Track], this_track, day):
    # Берем айдишники и меняем всю инфу местами, если у предыдущего нет ограничений
    for track in tracks:
        if track.day >= day:
            break
        if track.day < day and track.id != this_track.id:
            track, this_track = this_track, track
    return True
