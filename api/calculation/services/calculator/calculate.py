import datetime
import math
import time
from collections import defaultdict
from dataclasses import dataclass
from itertools import groupby
from typing import Any, List
from django.db.models import Min, Max, Sum, Count, Subquery, OuterRef

from calculation.models import Track, Order, ReadyPlate, Plate, Parameters, UnitPrice
from django.db import transaction


def profile_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"[PROFILE] {func.__name__} took {time.time() - start:.4f}s")
        return result

    return wrapper


# Классы для валидации и удобства разработки
@dataclass
class CustomTrack:
    id: int
    position: int
    width: int
    height: int
    concrete_class: str
    wire_bottom: int
    wire_top: int
    free_length: int
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
        params.production_lag,
    }


@profile_time
def calculate_plan():
    track_len, tail_len, production_lag = get_parameters()
    Track.recreate_tracks()
    tracks = Track.get_tracks()

    ready_plates = ReadyPlate.objects.all()
    use_ready_plates = 0
    for plate in ready_plates:
        need_plate = Plate.objects.filter(
            width=plate.width, height=plate.height,
            length=plate.length, concrete_class=plate.concrete_class,
            wire_bottom=plate.wire_bottom, wire_top=plate.wire_top
        ).first()
        if need_plate:
            need_plate.delete()
            use_ready_plates += 1

    if not ready_plates:
        print("Готовых плит нет.")

    unassigned_plates = list(Plate.objects.filter(track__isnull=True).order_by('width', 'height', 'length'))
    if not unassigned_plates:
        print("Нет плит для распределения.")
        return 0

    for t in tracks:
        print("Дорожка", t.id, "свободная длинна", t.free_length, "площадь", t.width, t.height, "день", t.day, "позиция", t.position, "заказчик", t.customer)
        track_setting = {
            "width": 0,
            "height": 0,
            "concrete_class": None,
            "wire_bottom": 0,
            "wire_top": 0
        }

        if not unassigned_plates:
            break
        min_plate_len = min(unassigned_plates, key=lambda x: x.length)
        if t.free_length < min_plate_len.length or t.customer:
            continue

        if t.free_length == track_len:
            add_plate_to_track(unassigned_plates[0], t)
            track_setting = {
                "width": unassigned_plates[0].width,
                "height": unassigned_plates[0].height,
                "concrete_class": unassigned_plates[0].concrete_class,
                "wire_bottom": unassigned_plates[0].wire_bottom,
                "wire_top": unassigned_plates[0].wire_top
            }
            print(f"Добавлена плита {unassigned_plates[0]} на дорожку {t}")
            unassigned_plates.pop(0)


        suitable_plates = [p for p in unassigned_plates if
                           p.width == track_setting['width'] and p.height == track_setting['height']]
        if not suitable_plates: continue

        while True:
            min_len_suitable = min(p.length for p in suitable_plates) if suitable_plates else float('inf')
            if t.free_length < min_len_suitable:
                break

            pl_to_set = search_need_plate(track_setting, suitable_plates, t.free_length)
            if not pl_to_set:
                break
            if pl_to_set.width == t.width and pl_to_set.height == t.height:
                if add_plate_to_track(pl_to_set, t):
                    unassigned_plates.remove(pl_to_set)
                    suitable_plates.remove(pl_to_set)
                    print(f"Добавлена плита {pl_to_set} на дорожку {t}")
                else:
                    print(f"Не удалось добавить плиту {pl_to_set} на дорожку {t}")
                    break

    # post_process_swap()

    post_calculating_deadlines()
    post_calculating_deadlines()
    post_calculating_deadlines()

    return 0

@profile_time
def post_process_swap():
    tracks = list(Track.objects.prefetch_related('plates').filter(plates__isnull=False).distinct())
    # Берем плиты из этой дорожки

    for i in range(len(tracks)):
        t1 = tracks[i]
        for j in range(i + 1, len(tracks)):
            t2 = tracks[j]
            config_a = get_dominant_config(t1)
            config_b = get_dominant_config(t2)
            if not config_a or not config_b:
                continue

            outliers_a = [
                    p for p in t1.plates.all()
                    if (p.concrete_class == config_b['concrete_class'] and
                        p.wire_bottom == config_b['wire_bottom'] and
                        p.wire_top == config_b['wire_top'])
                ]

            outliers_b = [
                    p for p in t2.plates.all()
                    if (p.concrete_class == config_a['concrete_class'] and
                        p.wire_bottom == config_a['wire_bottom'] and
                        p.wire_top == config_a['wire_top'])
                ]
            for plate_a in list(outliers_a):
                for plate_b in list(outliers_b):
                    # Условие для простого обмена
                    if plate_a.length == plate_b.length:
                        print(
                            f"Найден кандидат на обмен: {plate_a} (с дор. {t1.id}) <-> {plate_b} (с дор. {t2.id})")

                        # Выполняем обмен
                        plate_a.track = t2
                        plate_b.track = t1
                        plate_a.save()
                        plate_b.save()

                        print(f"Обмен выполнен: {plate_b} -> дор. {t1.id}, {plate_a} -> дор. {t2.id}")
                        outliers_a.remove(plate_a)
                        outliers_b.remove(plate_b)

def get_dominant_config(track):
    """
    Определяет доминирующую конфигурацию (бетон, арматура) для дорожки.
    Доминирующей считается та, у которой суммарная длина плит на дорожке максимальна.
    """
    if not track.plates.exists():
        return None

    # Агрегируем данные по плитам на дорожке
    configs = track.plates.values(
        'concrete_class', 'wire_bottom', 'wire_top'
    ).annotate(
        total_length=Sum('length'),
        plate_count=Count('id')
    ).order_by('-total_length', '-plate_count')

    dominant = configs.first()

    return {
        "concrete_class": dominant['concrete_class'],
        "wire_bottom": dominant['wire_bottom'],
        "wire_top": dominant['wire_top'],
    }

def add_plate_to_track(plate, track):
    plate.track = track
    try:
        plate.save()

        return True
    except Exception as e:
        print(f"Ошибка при добавлении плиты {plate} на дорожку {track}: {e}")
        return False

def search_need_plate(track_setting, plates, track_len):
    if not plates:
        return None


    best_plate = None
    min_distance = float('inf')

    for plate in plates:
        if track_len < plate.length:
            break
        # Проверяем на идеальное совпадение
        if (plate.width == track_setting['width'] and
                plate.height == track_setting['height'] and
                plate.concrete_class == track_setting['concrete_class'] and
                plate.wire_bottom == track_setting['wire_bottom'] and
                plate.wire_top == track_setting['wire_top']):
            return plate

        # Вычисляем "расстояние" для неидеального совпадения
        distance = 0

        # Вес для класса бетона (менее важный)
        distance += (1 if plate.concrete_class != track_setting['concrete_class'] else 0) * 2
        # Вес для арматуры
        distance += (1 if plate.wire_bottom != track_setting['wire_bottom'] else 0) * 6
        distance += (1 if plate.wire_top != track_setting['wire_top'] else 0) * 1

        # Обновляем лучшую плиту, если текущее расстояние меньше
        if distance < min_distance:
            min_distance = distance
            best_plate = plate

    return best_plate

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


@profile_time
def post_calculating():
    # берем дорожку, смотрим на хвост, если есть, то сдвигаем дорожку так далеко как можем(по дате)
    tracks = Track.get_tracks()
    max_tail_len = Parameters.get_solo().tail_length
    ft = Parameters.get_solo().force_tail
    if ft == 0:  # Если нет плит с дедлайном, то дорожку в конец
        i = 0
        while i in range(len(tracks) - 1):
            track = tracks[i]
            if track.customer:
                continue
            next_track = tracks[i + 1]
            if track.width != next_track.width or track.height != next_track.height:
                earliest_date = Plate.objects.filter(track=track.id).aggregate(
                    min_date=Min('deadline__date')
                )['min_date']
                if earliest_date is not None and track.free_length > max_tail_len:
                    swap_track_to_end(track)
                    continue

    if ft == 1:  #
        for track in tracks:
            if track.customer:
                continue
            earliest_date = Plate.objects.filter(track=track.id).aggregate(
                min_date=Min('deadline__date')
            )['min_date']
            if earliest_date is not None and track.free_length > max_tail_len:
                swap_track_to_end(track)
                continue

    if ft == 2:  #
        for track in tracks:
            # if had customers -> resume
            if track.customer:
                continue
            if track.free_length > max_tail_len:
                earliest_date = Plate.objects.filter(track=track.id).aggregate(
                    min_date=Min('deadline__date')
                )['min_date']
                if earliest_date is not None:
                    swap_track_to_deadline(track, earliest_date)
                else:
                    swap_track_to_end(track)


@profile_time
def fill_remaining_plates():
    """Добивает оставшиеся плиты на свободные дорожки, если они есть."""
    remaining_plates = list(Plate.objects.filter(track__isnull=True).order_by('width', 'height'))
    if not remaining_plates:
        return

    free_tracks = list(Track.objects.all().order_by('day', 'position'))
    for plate in remaining_plates:
        for track in free_tracks:
            if plate.length > track.free_length:
                continue
            add_plate_to_track(plate, track)
            break


@profile_time
def swap_track_to_end(this_track):
    tracks = Track.objects.filter(day__gt=this_track.day).order_by("day", "position")

    if not tracks.exists():
        return True  # Нет дорожек для обмена, завершаем

    # Сохраняем исходные значения this_track
    current_day = this_track.day
    current_position = this_track.position

    # Перемещаем this_track к началу, последовательно меняя day и position
    for track in tracks:
        if track.id != this_track.id:  # На случай, если this_track уже в списке
            # Сохраняем значения текущей дорожки
            next_day = track.day
            next_position = track.position

            # Обновляем значения текущей дорожки
            track.day = current_day
            track.position = current_position
            track.save()

            # Обновляем значения this_track
            current_day = next_day
            current_position = next_position

    # Сохраняем финальные значения для this_track
    this_track.day = current_day
    this_track.position = current_position
    this_track.save()

    return True


@profile_time
def swap_track_to_start(this_track) -> bool:
    # Получаем дорожки с меньшим днем, сортируем по убыванию day и position
    tracks = Track.objects.filter(day__lt=this_track.day).order_by("-day", "-position")

    if not tracks.exists():
        return True  # Нет дорожек для обмена, завершаем

    # Сохраняем исходные значения this_track
    current_day = this_track.day
    current_position = this_track.position

    # Перемещаем this_track к началу, последовательно меняя day и position
    for track in tracks:
        if track.id != this_track.id:  # На случай, если this_track уже в списке
            # Сохраняем значения текущей дорожки
            next_day = track.day
            next_position = track.position

            # Обновляем значения текущей дорожки
            track.day = current_day
            track.position = current_position
            track.save()

            # Обновляем значения this_track
            current_day = next_day
            current_position = next_position

    # Сохраняем финальные значения для this_track
    this_track.day = current_day
    this_track.position = current_position
    this_track.save()

    return True


@profile_time
def swap_track_to_deadline(this_track, deadline):
    # Берем айдишники и меняем всю инфу местами, если у предыдущего нет ограничений

    # Получаем дорожки с днем меньше целевой даты, сортируем по убыванию day и возрастанию position
    filtered_tracks = Track.objects.filter(day__gt=this_track.day).order_by("day", "position")

    if not filtered_tracks.exists():
        return False

    # Сохраняем исходные значения this_track
    current_day = this_track.day
    current_position = this_track.position

    # Перемещаем this_track к позиции перед target_date, меняя day и position
    for track in filtered_tracks:
        if track.id != this_track.id:  # Пропускаем, если это та же дорожка
            # Сохраняем значения текущей дорожки
            next_day = track.day
            next_position = track.position

            # Обновляем значения текущей дорожки
            track.day = current_day
            track.position = current_position
            track.save()

            # Обновляем значения для следующей итерации
            current_day = next_day
            current_position = next_position

    # Сохраняем финальные значения для this_track
    this_track.day = current_day
    this_track.position = current_position
    this_track.save()

    return True


@profile_time
def swap_track_to_start_to_deadline(tracks, this_track: Track, deadline: datetime.date) -> bool:
    # Вычисляем целевую дату (за 2 дня до дедлайна)
    target_date = deadline - datetime.timedelta(days=1)

    # Получаем дорожки с днем меньше целевой даты, сортируем по убыванию day и возрастанию position
    filtered_tracks = tracks.filter(day__lt=target_date).order_by("-day", "position")

    if not filtered_tracks.exists():
        return False

    # Сохраняем исходные значения this_track
    current_day = this_track.day
    current_position = this_track.position

    # Перемещаем this_track к позиции перед target_date, меняя day и position
    for track in filtered_tracks:
        if track.id != this_track.id:  # Пропускаем, если это та же дорожка
            # Сохраняем значения текущей дорожки
            next_day = track.day
            next_position = track.position

            # Обновляем значения текущей дорожки
            track.day = current_day
            track.position = current_position
            track.save()

            # Обновляем значения для следующей итерации
            current_day = next_day
            current_position = next_position

    # Сохраняем финальные значения для this_track
    this_track.day = current_day
    this_track.position = current_position
    this_track.save()

    return True


@profile_time
def post_calculating_deadlines():
    """Переставляет дорожки (меняет дни) так, чтобы дедлайны не «горели» с учётом производственного лага."""
    tracks = Track.objects.all().order_by('day', 'position')
    for track in tracks:
        if track.customer:
            continue

        earliest_date = Plate.objects.filter(track=track.id).aggregate(
            min_date=Min('deadline__date')
        )['min_date']
        if earliest_date is None:
            continue
        earliest_date = earliest_date - datetime.timedelta(days=Parameters.get_solo().production_lag)

        if earliest_date <= track.day:
            swap_track_to_start_to_deadline(Track.objects.all(), track, earliest_date)

    tracks = Track.objects.all().order_by('day', 'position')
    for track in tracks:
        if track.customer:
            continue

        earliest_date = Plate.objects.filter(track=track.id).aggregate(
            min_date=Min('deadline__date')
        )['min_date']
        if earliest_date is None:
            continue
        earliest_date = earliest_date - datetime.timedelta(days=Parameters.get_solo().production_lag)

        if earliest_date < datetime.date.today():
            print(f"Дорожка {track.id} сгорела по дедлайну {earliest_date}.")
            swap_track_to_start(track)


@profile_time
def compact_days():
    """Уплотняет дни дорожек, устраняя разрывы, с учётом production_lag."""
    params = Parameters.get_solo()
    production_lag = params.production_lag

    # Берём только те дорожки, где реально есть плиты
    used_tracks = Track.objects.filter(plates__isnull=False).distinct().order_by("day", "position")
    if not used_tracks.exists():
        print("Нет занятых дорожек — уплотнять нечего.")
        return

    # первая дата производства
    first_day = used_tracks.first().day
    current_day = first_day

    with transaction.atomic():
        prev_day = None
        for day in sorted(set(t.day for t in used_tracks)):
            day_tracks = Track.objects.filter(day=day).order_by("position")

            # если пропуск дней, переносим на ближайший current_day
            if prev_day and (day - prev_day).days > 1:
                day_tracks_to_move = list(day_tracks)
                for track in day_tracks_to_move:
                    # проверяем все плиты на дорожке
                    valid = True
                    for plate in track.plates.all():
                        if plate.deadline and plate.deadline.date:
                            latest_day = plate.deadline.date - datetime.timedelta(days=production_lag)
                            if current_day > latest_day:
                                valid = False
                                break

                    if valid:
                        track.day = current_day
                        track.save()

                current_day = current_day + datetime.timedelta(days=1)
            else:
                current_day = day
            prev_day = current_day
