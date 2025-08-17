import datetime
import time
from collections import defaultdict
from typing import Any, List
from django.db.models import Min, Max

from calculation.models import Track, Order, ReadyPlate, Plate, Parameters
from django.db import transaction


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
        params.production_lag,
    }

@profile_time
def claster_plan():
    track_len, tail_len, production_lag = get_parameters()

    Track.recreate_tracks()
    tracks = list(Track.get_tracks())

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

    plates_from_db = Plate.objects.filter(track__isnull=True)

    tasks = []
    for p in plates_from_db:
        # дедлайн может быть None → заменяем на максимально возможную дату
        deadline_date = p.deadline.date if (p.deadline and p.deadline.date) else datetime.date.max
        tasks.append({
            'length': p.length,
            'width': p.width,
            'height': p.height,
            'concrete_class': p.concrete_class,
            'wire_top': p.wire_top,
            'wire_bottom': p.wire_bottom,
            'deadline': deadline_date,
            "p": p
        })

    if not tasks:
        print("Нет плит для планирования.")
        return

    # базовая дата — на 2 дня раньше самого раннего дедлайна
    min_deadline = min(t['deadline'] for t in tasks)
    base_date = min_deadline

    # вычисляем последний возможный день производства
    for t in tasks:
        d = t['deadline'] - datetime.timedelta(days=production_lag)
        t['last_day'] = (d - base_date).days

    # сортируем задачи по last_day, чтобы приоритет у горящих заказов
    tasks.sort(key=lambda x: x['last_day'])

    # кластеризация по (width, height)
    clusters = defaultdict(list)
    for t in tasks:
        key = (t['width'], t['height'])
        clusters[key].append(t)

    # сортировка кластеров по самому раннему дедлайну
    cluster_keys = sorted(clusters.keys(), key=lambda cl: min(p['last_day'] for p in clusters[cl]))

    # планирование: идём по кластерам, начиная с самых срочных
    for cl in cluster_keys:
        plates = clusters[cl]
        plates.sort(key=lambda x: x['last_day'])  # внутри кластера тоже срочные вперёд
        for track in tracks:
            if track.customer:
                continue
            if track.free_length < track_len:
                continue
            loaded = pack_track(plates, track, track_len)
            if not plates:
                break  # все плиты кластера распределили



    post_calculating()
    # for i in range(10):
    #     post_calculating()

    post_calculating_deadlines()
    compact_days()


def pack_track(plist, track, track_len):
    cap = track_len  # мм
    loaded = []

    # сгруппируем по классу бетона
    from itertools import groupby
    plist.sort(key=lambda x: (x['concrete_class'], x['last_day'], -x['length']))

    for concrete_class, group in groupby(plist, key=lambda x: x['concrete_class']):
        group = list(group)
        for p in group[:]:
            if p['length'] <= cap:
                loaded.append(p)
                cap -= p['length']
                add_plate_to_track(p['p'], track)
                plist.remove(p)

    return loaded


def add_plate_to_track(plate, track):
    plate.track = track
    try:
        plate.save()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении плиты {plate} на дорожку {track}: {e}")
        return False




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
                    swap_track_to_end(tracks, track)
                    continue

    if ft == 1:  #
        for track in tracks:
            if track.customer:
                continue
            earliest_date = Plate.objects.filter(track=track.id).aggregate(
                min_date=Min('deadline__date')
            )['min_date']
            if earliest_date is not None and track.free_length > max_tail_len:
                swap_track_to_end(tracks, track)
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
                    swap_track_to_deadline(tracks, track, earliest_date)
                else:
                    swap_track_to_end(tracks, track)

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
def swap_track_to_end(tracks, this_track):
    for track in tracks:
        if this_track.id != track.id:
            track.id, this_track.id = this_track.id, track.id
            track.save()
            this_track.save()
    return True


@profile_time
def swap_track_to_deadline(tracks: List[Track], this_track, day):
    # Берем айдишники и меняем всю инфу местами, если у предыдущего нет ограничений
    for track in tracks:
        if track.day >= day:
            break
        if track.day < day and track.id != this_track.id:
            track.id, this_track.id = this_track.id, track.id
            track.save()
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


@profile_time
def post_calculating_deadlines():
    """Переставляет дорожки (меняет дни) так, чтобы дедлайны не «горели» с учётом производственного лага."""
    from django.utils.timezone import make_naive

    tracks = list(Track.get_tracks())
    updated_tracks = []

    parameters = Parameters.get_solo()
    production_lag = parameters.production_lag or 0

    deadlines = {}
    for track in tracks:
        agg = Plate.objects.filter(track=track.id).aggregate(
            min_date=Min('deadline__date'),
            max_date=Max('deadline__date')
        )
        min_date = agg.get('min_date')
        if min_date:
            # Приводим к naive-дате для безопасного сравнения с day (если он date)
            if hasattr(min_date, 'tzinfo'):
                min_date = make_naive(min_date)
            critical_date = min_date - datetime.timedelta(days=production_lag)
        else:
            critical_date = None
        deadlines[track.id] = {
            'min': min_date,
            'critical': critical_date
        }

    for i, this_track in enumerate(tracks):
        crit_deadline_i = deadlines.get(this_track.id, {}).get('critical')
        if crit_deadline_i is None:
            continue
        try:
            if this_track.day <= crit_deadline_i:
                continue  # ещё не горит
        except Exception:
            continue

        preferred_j = None
        fallback_j = None

        for j, other in enumerate(tracks):
            if i == j:
                continue
            crit_deadline_j = deadlines.get(other.id, {}).get('critical')

            # other.day должен позволить this_track не сгореть
            cond1 = True
            try:
                cond1 = (other.day <= crit_deadline_i)
            except Exception:
                cond1 = False
            if not cond1:
                continue

            # this_track.day должен позволить other не сгореть
            cond2 = True
            if crit_deadline_j is not None:
                try:
                    cond2 = (this_track.day <= crit_deadline_j)
                except Exception:
                    cond2 = False
            if not cond2:
                continue

            if getattr(other, 'width', None) == getattr(this_track, 'width', None) and \
               getattr(other, 'height', None) == getattr(this_track, 'height', None):
                preferred_j = j
                break

            if fallback_j is None:
                fallback_j = j

        chosen_j = preferred_j if preferred_j is not None else fallback_j
        if chosen_j is not None:
            other = tracks[chosen_j]
            this_track.day, other.day = other.day, this_track.day
            this_track.save()
            other.save()
            updated_tracks.extend((this_track, other))

    # Пересчёт позиций
    day_track_indices = defaultdict(list)
    for idx, track in enumerate(tracks):
        day_track_indices[track.day].append((idx, track))
    for _, idx_tracks in day_track_indices.items():
        sorted_tracks = [track for _, track in sorted(idx_tracks, key=lambda x: x[0])]
        for pos, track in enumerate(sorted_tracks):
            track.position = pos

    if updated_tracks:
        unique_updates = {t.id: t for t in updated_tracks}.values()
        Track.objects.bulk_update(list(unique_updates), ['position', 'day'])

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
