import datetime
import time
from collections import defaultdict
from typing import Any, List
from django.db.models import Min, Max

from ortools.sat.python import cp_model
from collections import namedtuple

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

    Track.recreate_tracks()

    ready_plates = ReadyPlate.objects.all()
    use_ready_plates = 0
    for plate in ready_plates:
        need_plate = Plate.objects.filter(width=plate.width, height=plate.height,
                                          length=plate.length, concrete_class=plate.concrete_class,
                                          wire_bottom=int(plate.wire_bottom), wire_top=int(plate.wire_top)).first()
        if need_plate:
            need_plate.delete()
            plate.used_in_order = need_plate.deadline.order
            plate.save()
            use_ready_plates += 1

    if not ready_plates:
        print("Готовых плит нет.")

    tracks_with_customers = Track.objects.filter(customer__isnull=False).order_by('day', 'position')

    for track in tracks_with_customers:
        order = Order.objects.filter(customer=track.customer)
        plates = Plate.objects.filter(deadline__order__in=order, track__isnull=True)
        if not plates: break
        for plate in plates:
            if track.free_length == track_len:
                plate = plates[0]
                plate.track = track
                plate.save()
            else:
                if plate.length <= track.free_length and plate.width == track.width and plate.height == track.height:
                    plate.track = track
                    plate.save()
        if track_len-track.free_length > 5000:
            plus_plates = Plate.objects.filter(width=track.width, height=track.height, track__isnull=True)
            if not plus_plates: print("нечем дополнять")
            for plate in plus_plates:
                if plate.length <= track.free_length:
                    plate.track = track
                    plate.save()
        track.save()



    create_plan()

    # fill_remaining_plates()  # Новый шаг

    print({
        "plan": True,
        "Use_ready_plates": use_ready_plates,
    })


@profile_time
def create_plan():
    """Основная функция - алгоритм распределения плит по дорожкам
    """


    track_len, tail_len = get_parameters()
    tracks = Track.get_tracks()
    tracks_with_customers = [t for t in tracks if t.customer is not None]
    print(tracks_with_customers)
    customers_with_tracks = [t.customer for t in tracks_with_customers]
    print(customers_with_tracks)
    plates = Plate.objects.filter(track__isnull=True).exclude(
        id__in=Plate.objects.filter(track__customer__in=customers_with_tracks).values_list("id", flat=True)
    )

    # Разделяем плиты на две группы
    plates_with_deadline = [p for p in plates if p.deadline.date is not None]
    plates_without_deadline = [p for p in plates if p.deadline.date is None]

    plates_with_deadline.sort(key=lambda p: (p.deadline.date, p.width, p.height, p.wire_bottom))
    plates_without_deadline.sort(key=lambda p: (p.width, p.height))

    if not plates_with_deadline and not plates_without_deadline:
        print("Нет плит для размещения. План пуст.")
        return True

    placed_plate_ids = set()

    for track in tracks:
        remaining_length = track.free_length
        current_track_properties = None
        if track.customer is not None:
            tmp_need_plates = list(Plate.objects.filter(deadline__order__customer=track.customer))
            tmp_need_plates.sort(key=lambda p: (p.width, p.height, p.wire_bottom))
            current_track_properties = fill_track(tmp_need_plates, placed_plate_ids, remaining_length, track, current_track_properties)

        else:
            # 1. Сначала пытаемся ставить плиты с дедлайнами
            current_track_properties = fill_track(plates_with_deadline, placed_plate_ids, remaining_length, track, current_track_properties)

        # 2. Если что-то ещё осталось – добиваем плитами без дедлайнов
        if track.free_length > 0:
            current_track_properties = fill_track(plates_without_deadline, placed_plate_ids, track.free_length, track, current_track_properties)

    # Плиты, которые не удалось разместить
    unplaced_plates = [p for p in plates if p.id not in placed_plate_ids]
    if unplaced_plates:
        print(f"{len(unplaced_plates)} плит не удалось разместить.")

    # post_calculating()
    post_calculating_deadlines()
    post_calculating_deadlines()
    post_calculating_deadlines()
    regroup_plates_by_wire()

    return True



def fill_track(plates_list, placed_plate_ids, remaining_length, track, current_track_properties):
    for plate in plates_list:
        if plate.id in placed_plate_ids:
            continue

        # Жёсткая проверка на вместимость
        if plate.length > track.free_length or plate.length > remaining_length:
            continue

        plate_properties = (plate.width, plate.height)

        if current_track_properties is None:
            current_track_properties = plate_properties
        elif plate_properties != current_track_properties:
            continue

        add_plate_to_track(plate, track)
        placed_plate_ids.add(plate.id)

        # Пересчёт после добавления
        remaining_length = track.free_length

        if remaining_length <= 0:
            break

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

    # ❌ Убираем полное обнуление Plate.track
    # Plate.objects.all().update(track=None)

    available_tasks = tasks.copy()
    previous_properties = None
    for position_track in all_tracks:
        day = position_track.day
        candidates = [task for task in available_tasks if task['min_deadline'] is None or task['min_deadline'] >= day]
        if not candidates:
            continue
        if previous_properties:
            matching = [task for task in candidates if (task['width'], task['height']) == previous_properties]
            chosen_task = matching[0] if matching else candidates[0]
        else:
            chosen_task = candidates[0]
        for plate in chosen_task['plates']:
            if plate.length > position_track.free_length:
                continue
            add_plate_to_track(plate, position_track)
        previous_properties = (chosen_task['width'], chosen_task['height'])
        available_tasks.remove(chosen_task)

    if available_tasks:
        print(f"Не удалось разместить {len(available_tasks)} заданий")

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
        if track.customer or track.is_manual:
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
        if track.customer or track.is_manual:
            continue
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
        if crit_deadline_i is None and not this_track.customer:
            continue
        try:
            if this_track.day <= crit_deadline_i:
                continue  # ещё не горит
        except Exception:
            continue

        preferred_j = None
        fallback_j = None

        for j, other in enumerate(tracks):
            if i == j and not other.customer:
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
            if other.customer or this_track.customer:
                continue
            this_track.day, other.day = other.day, this_track.day
            this_track.customer, other.customer = other.customer, this_track.customer
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
            if not track.customer: track.position = pos

    if updated_tracks:
        unique_updates = {t.id: t for t in updated_tracks}.values()
        Track.objects.bulk_update(list(unique_updates), ['position', 'day'])


# Убедитесь, что эти импорты присутствуют в начале вашего файла
from collections import namedtuple, defaultdict
# +++ НАЧАЛО: Вспомогательная функция-решатель с OR-Tools +++

# Определяем структуру для передачи данных в решатель.
# Это делает код чище и позволяет отделить логику решателя от Django-моделей.
Slab = namedtuple('Slab', ['id', 'length', 'wire_top', 'wire_bottom'])

from collections import defaultdict
from datetime import date
from ortools.sat.python import cp_model


def solve_slab_grouping_ortools(slabs_data: list[Slab], num_available_tracks: int, track_capacity: int, time_limit_seconds: float = 30.0):
    """
    Улучшенная версия:
    - минимизирует суммарные разницы (max_on_track - slab_wire) для top и bottom,
      используя линейную модель на уровне каждой плиты (cost_ij).
    - сужает домены max_wire_on_track до реальных существующих значений.
    """
    model = cp_model.CpModel()
    num_slabs = len(slabs_data)
    if num_slabs == 0:
        return {}

    # --- предварительные множества значений проволоки ---
    top_values = sorted({s.wire_top for s in slabs_data})
    bottom_values = sorted({s.wire_bottom for s in slabs_data})
    min_top, max_top = top_values[0], top_values[-1]
    min_bottom, max_bottom = bottom_values[0], bottom_values[-1]

    # 1) переменные размещения x[i,j]
    x = {}
    for i in range(num_slabs):
        for j in range(num_available_tracks):
            x[(i, j)] = model.NewBoolVar(f'x_slab{i}_track{j}')

    # каждая плита ровно на одной дорожке
    for i in range(num_slabs):
        model.AddExactlyOne([x[(i, j)] for j in range(num_available_tracks)])

    # длина по дорожке <= вместимость
    for j in range(num_available_tracks):
        model.Add(sum(slabs_data[i].length * x[(i, j)] for i in range(num_slabs)) <= track_capacity)

    # 2) максимумы проволоки на дорожке: ограничим домен реальными значениями
    # используем Domain.FromValues для ужатия доменов
    max_wire_top_on_track = []
    max_wire_bottom_on_track = []
    for j in range(num_available_tracks):
        if len(top_values) == 1:
            # если только одно значение, можно взять простой NewIntVar
            max_top_var = model.NewIntVar(min_top, max_top, f'max_top_track_{j}')
        else:
            max_top_var = model.NewIntVarFromDomain(cp_model.Domain.FromValues(top_values), f'max_top_track_{j}')
        if len(bottom_values) == 1:
            max_bottom_var = model.NewIntVar(min_bottom, max_bottom, f'max_bottom_track_{j}')
        else:
            max_bottom_var = model.NewIntVarFromDomain(cp_model.Domain.FromValues(bottom_values), f'max_bottom_track_{j}')

        max_wire_top_on_track.append(max_top_var)
        max_wire_bottom_on_track.append(max_bottom_var)

    # 3) Связь: если плита i назначена на дорожку j, то max_on_track >= её значение проволоки
    for j in range(num_available_tracks):
        for i in range(num_slabs):
            model.Add(max_wire_top_on_track[j] >= slabs_data[i].wire_top).OnlyEnforceIf(x[(i, j)])
            model.Add(max_wire_bottom_on_track[j] >= slabs_data[i].wire_bottom).OnlyEnforceIf(x[(i, j)])

    # 4) Линеаризация издержек на уровне каждой плиты (cost_top_ij, cost_bottom_ij)
    max_top_range = max_top - min_top
    max_bottom_range = max_bottom - min_bottom
    cost_top = {}
    cost_bottom = {}
    for i in range(num_slabs):
        for j in range(num_available_tracks):
            # максимум возможной разницы — диапазон значений
            ct = model.NewIntVar(0, max_top_range, f'cost_top_s{i}_t{j}')
            cb = model.NewIntVar(0, max_bottom_range, f'cost_bottom_s{i}_t{j}')
            cost_top[(i, j)] = ct
            cost_bottom[(i, j)] = cb

            # если плита i на дорожке j -> cost == max_on_track - slab_wire
            # иначе cost == 0
            model.Add(ct == max_wire_top_on_track[j] - slabs_data[i].wire_top).OnlyEnforceIf(x[(i, j)])
            model.Add(ct == 0).OnlyEnforceIf(x[(i, j)].Not())

            model.Add(cb == max_wire_bottom_on_track[j] - slabs_data[i].wire_bottom).OnlyEnforceIf(x[(i, j)])
            model.Add(cb == 0).OnlyEnforceIf(x[(i, j)].Not())

    # 5) Целевая функция: минимизировать суммарные издержки top + bottom
    objective_terms = []
    for i in range(num_slabs):
        for j in range(num_available_tracks):
            objective_terms.append(cost_top[(i, j)])
            objective_terms.append(cost_bottom[(i, j)])
    model.Minimize(sum(objective_terms))

    # 6) Параметры решателя и запуск
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    # совет: можно включить многопоточность, если нужно ускорить поиск
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        # собираем результат: дорожки -> список плит
        result = {f'track_{j}': [] for j in range(num_available_tracks)}
        for j in range(num_available_tracks):
            for i in range(num_slabs):
                if solver.Value(x[(i, j)]) == 1:
                    result[f'track_{j}'].append(slabs_data[i])
        # отфильтруем пустые дорожки
        result = {k: v for k, v in result.items() if v}
        print(f"РЕЗУЛЬТАТ: статус {solver.StatusName(status)}, целевая = {solver.ObjectiveValue()}")
        return result
    else:
        print("РЕЗУЛЬТАТ: решение не найдено")
        return None

# +++ КОНЕЦ: Вспомогательная функция-решатель с OR-Tools +++



# +++ КОНЕЦ: Вспомогательная функция-решатель с OR-Tools +++


@profile_time
def regroup_plates_by_wire():
    """
    Перераспределяет плиты между дорожками для минимизации расхождений по проволоке
    с использованием OR-Tools для оптимального решения.
    """
    print("--- Запуск перегруппировки плит по проволоке (с OR-Tools) ---")

    try:
        track_len = Parameters.get_solo().road_length
        if not isinstance(track_len, (int, float)) or track_len <= 0:
            print(f"ОШИБКА: Некорректное значение длины дорожки: {track_len}")
            return
    except (ValueError, TypeError) as e:
        print(f"Не удалось получить параметры. Проверьте функцию get_parameters(). Ошибка: {e}")
        return

    all_plates_to_update = []

    days = Track.objects.values_list('day', flat=True).distinct().order_by('day')

    for day in days:
        tracks_on_day = Track.objects.filter(
            day=day,
            customer__isnull=True,
            is_manual=False
        ).prefetch_related('plates')

        dimension_groups = defaultdict(list)
        for track in tracks_on_day:
            if track.width is not None and track.height is not None:
                dimension_groups[(track.width, track.height)].append(track)

        for dimensions, tracks_in_group in dimension_groups.items():
            width, height = dimensions
            print(f"\nОбработка группы: День {day}, Размеры {width}x{height}, Дорожек: {len(tracks_in_group)}")

            # 1. Собираем все плиты из группы
            all_plates_in_group = []
            for track in tracks_in_group:
                all_plates_in_group.extend(list(track.plates.all()))

            if not all_plates_in_group:
                print("Плит в группе нет, пропускаем.")
                continue

            print(f"Всего плит для перераспределения: {len(all_plates_in_group)}")

            # 2. Подготовка данных для решателя
            # Создаем карту "ID плиты -> объект Plate" для быстрой обратной связи
            plate_map = {p.id: p for p in all_plates_in_group}

            # Конвертируем Django-объекты в простой формат данных для решателя
            slabs_for_solver = [
                Slab(
                    id=plate.id,
                    length=int(plate.length),
                    wire_top=int(plate.wire_top),
                    wire_bottom=int(plate.wire_bottom)
                )
                for plate in all_plates_in_group
            ]

            # 3. Вызов решателя OR-Tools
            solution = solve_slab_grouping_ortools(
                slabs_data=slabs_for_solver,
                num_available_tracks=len(tracks_in_group),
                track_capacity=track_len
            )

            # 4. Обработка результата
            if solution:
                # Решение найдено, распределяем плиты по реальным дорожкам

                # Сначала "снимаем" все плиты, чтобы избежать конфликтов
                for plate in all_plates_in_group:
                    plate.track = None

                # Сопоставляем виртуальные дорожки из решения с реальными
                real_tracks = list(tracks_in_group)

                # Перебираем группы плит из решения
                for i, (virtual_track_name, slabs_on_track) in enumerate(solution.items()):
                    if i < len(real_tracks):
                        target_track = real_tracks[i]
                        # Для каждой плиты в группе назначаем реальную дорожку
                        for slab in slabs_on_track:
                            plate_to_update = plate_map[slab.id]
                            plate_to_update.track = target_track
                    else:
                        # Эта ситуация не должна возникать, если логика верна
                        print(f"!!! ПРЕДУПРЕЖДЕНИЕ: Решатель вернул больше групп плит, чем доступно дорожек!")

            else:
                # Решение не найдено, значит, плиты не помещаются на дорожки.
                # Оставляем их нераспределенными.
                print(f"!!! ПРЕДУПРЕЖДЕНИЕ: Не удалось найти решение для группы {width}x{height} в день {day}. Все {len(all_plates_in_group)} плит станут нераспределенными.")
                for plate in all_plates_in_group:
                    plate.track = None

            # Добавляем все обработанные плиты (и размещенные, и нет) в общий список на обновление
            all_plates_to_update.extend(all_plates_in_group)

    # После обработки всех дней и групп, одним запросом обновляем все изменения
    if all_plates_to_update:
        unique_plates_to_update = {p.id: p for p in all_plates_to_update}.values()
        Plate.objects.bulk_update(list(unique_plates_to_update), ['track'])
        print(f"\n--- Перегруппировка завершена. Обновлено состояние {len(unique_plates_to_update)} плит. ---")
    else:
        print("\n--- Перегруппировка завершена. Изменений не было. ---")
