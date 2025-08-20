import datetime
import time
from collections import defaultdict
from itertools import groupby
from typing import Any, List
from django.db.models import Min, Max
from django.db.models import Subquery, OuterRef

from calculation.models import Track, Order, ReadyPlate, Plate, Parameters, UnitPrice
from django.db import transaction
from ortools.sat.python import cp_model


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
            'length': int(p.length),
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

    # вычисляем последний возможный день производства
    for t in tasks:
        t['deadline'] = t['deadline'] - datetime.timedelta(days=production_lag)

    # сортируем задачи по deadline, чтобы приоритет у горящих заказов
    tasks.sort(key=lambda x: x['deadline'])

    # кластеризация по (width, height)
    clusters = defaultdict(list)
    for t in tasks:
        key = (t['width'], t['height'])
        clusters[key].append(t)

    # сортировка кластеров по самому раннему дедлайну
    cluster_keys = sorted(clusters.keys(), key=lambda cl: min(p['deadline'] for p in clusters[cl]))

    # планирование: идём по кластерам, начиная с самых срочных
    for cl in cluster_keys:
        print(f"Работаем с кластером {cl}")
        plist = clusters[cl]
        plist.sort(key=lambda x: x['deadline'])  # внутри кластера тоже срочные вперёд

        available_tracks = [track for track in tracks if not track.customer and track.free_length >= track_len]
        max_bins = len(available_tracks)
        if max_bins == 0:
            continue

        n = len(plist)
        if n == 0:
            continue
        total_length = sum(p['length'] for p in plist)
        max_capacity = track_len * max_bins
        if total_length > max_capacity:
            print(
                f"Невозможно упаковать все {n} плиты в кластере {cl}: общая длина {total_length} мм превышает ёмкость {max_capacity} мм.")
            # Здесь можно добавить логику: отложить плиты или увеличить max_bins, если возможно
            continue  # Или обработать частично
        # Настройка модели OR-Tools
        model = cp_model.CpModel()

        assign = [[model.NewBoolVar(f'assign_{i}_{b}') for b in range(max_bins)] for i in range(n)]
        bin_used = [model.NewBoolVar(f'bin_used_{b}') for b in range(max_bins)]

        for b in range(max_bins):
            for i in range(n):
                model.Add(bin_used[b] >= assign[i][b])

        # Ограничение по вместимости
        for b in range(max_bins):
            model.Add(sum(assign[i][b] * plist[i]['length'] for i in range(n)) <= track_len * bin_used[b])

        # Обязательная упаковка ВСЕХ плит: каждая плита должна быть назначена ровно на одну дорожку
        for i in range(n):
            model.Add(sum(assign[i][b] for b in range(max_bins)) == 1)
        print(f"Плит в кластере: {n}")
        # Атрибуты для разнородности
        attrs = ['concrete_class', 'wire_bottom']
        possible = {attr: set(p[attr] for p in plist) for attr in attrs}

        used = {}
        for attr in attrs:
            used[attr] = {}
            for val in possible[attr]:
                used[attr][val] = [model.NewBoolVar(f'used_{attr}_{val}_{b}') for b in range(max_bins)]

        for attr in attrs:
            for val in possible[attr]:
                for b in range(max_bins):
                    plates_with_val = [i for i in range(n) if plist[i][attr] == val]
                    for i in plates_with_val:
                        model.Add(used[attr][val][b] >= assign[i][b])

        # Штраф за разнородность
        print("Штрафуем за разнородность")
        penalty = 0
        for b in range(max_bins):
            for attr in attrs:
                weight = 100 if attr == 'wire_bottom' else 1  # Увеличенный вес для wire_bottom
                penalty += weight * sum(used[attr][val][b] for val in possible[attr])

        # Штраф за остаток свободной длины
        remaining_length = []
        for b in range(max_bins):
            used_length = sum(assign[i][b] * plist[i]['length'] for i in range(n))
            remaining = model.NewIntVar(0, track_len, f'remaining_{b}')
            model.Add(remaining == track_len * bin_used[b] - used_length)
            remaining_length.append(remaining)

        # Веса для приоритета упаковки (более срочные - больший вес)
        weights = [n - i for i in range(n)]  # наивысший для первого (самого срочного)
        print("Веса для приоритета упаковки")
        print(weights)

        # Коэффициенты для иерархии
        M4 = 20  # Вес для штрафа за остаток длины
        M3 = 400 # штраф за разнородность
        M2 = 50 # балансирует минимизацию числа дорожек


        # Objective
        sum_remaining = sum(remaining_length[b] for b in range(max_bins))
        model.Minimize(
            + M2 * sum(bin_used)  # минимизация числа дорожек
            + M3 * penalty  # минимизация разнородности
            + M4 * sum_remaining  # минимизация остатка
        )

        # Решение
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = 42
        solver.parameters.relative_gap_limit = 0.05
        solver.parameters.max_time_in_seconds = 1800  # ToDo Убери!!!
        status = solver.Solve(model)

        print(f"Status: {solver.StatusName(status)}")
        print(f"Objective value: {solver.ObjectiveValue()}")
        print(f"Penalty (heterogeneity): {solver.Value(penalty)}")
        print(f"Remaining length: {solver.Value(sum_remaining)}")
        print(f"Bins used: {sum(solver.Value(bin_used[b]) for b in range(max_bins))}")

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"Использовано {sum(solver.Value(bin_used[b]) for b in range(max_bins))} дорожек")
            assignments = defaultdict(list)
            for b in range(max_bins):
                for i in range(n):
                    if solver.Value(assign[i][b]):
                        assignments[b].append(i)

            for b in assignments:
                if assignments[b]:
                    track = available_tracks.pop(0)
                    for i in assignments[b]:
                        add_plate_to_track(plist[i]['p'], track)
                        print(f"{i}. Плита {plist[i]['p']} упакована на дорожку {track}")

        # Если некоторые не упакованы, они остаются для следующих итераций или ручной обработки

    # post_calculating()
    # for i in range(10):
    #     post_calculating()

    post_calculating_deadlines()


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
