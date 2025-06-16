import json
from datetime import datetime, timedelta

import requests
from django.db.models import F

from calculation.models import AvailableTrack, DailyRetooling, DailyRetoolingChanges, Inventory, LeftReadyPlate, Order, \
    Parameters, \
    ProductionDay, ProductionDayPlate, ProductionPlan, RetoolingInfo, UnitPrice, UnplacedPlate, UsedReadyPlate
from calculation.utils import DecimalEncoder


def clear_old_data(date_from):
    ProductionPlan.objects.all().delete()
    ProductionDay.objects.all().delete()
    LeftReadyPlate.objects.all().delete()
    RetoolingInfo.objects.all().delete()
    DailyRetooling.objects.all().delete()
    DailyRetoolingChanges.objects.all().delete()
    UnplacedPlate.objects.all().delete()
    UsedReadyPlate.objects.all().delete()
    AvailableTrack.objects.filter(date__lt=date_from).delete()


def prepare_data(date_from, date_to):
    params = Parameters.get_solo()
    unit_plate_prices = [
        {
            'name': plate.concrete_class,
            'price': plate.price
        }
        for plate in UnitPrice.objects.filter(unit=UnitPrice.UnitTypeChoice.PLATE)
    ]
    unit_wire_price = UnitPrice.objects.filter(unit=UnitPrice.UnitTypeChoice.WIRE).first().price
    unit_retooling_price = UnitPrice.objects.filter(unit=UnitPrice.UnitTypeChoice.RETOOLING).first().price
    inventory = Inventory.objects.all()
    available_tracks = list(AvailableTrack.get_tracks(date_from, date_to).annotate(day=F('date')).values('day', 'count'))
    available_tracks = [{'day': str(t['day']), 'count': t['count']} for t in available_tracks]
    orders_numbers = sorted(set(Order.objects.all().values_list('order_number', flat=True)))
    orders_data = []
    for order_number in orders_numbers:
        order_data = {
            "number": order_number,
            "production_days": 0,
            "completion_dates": []
        }
        order_dates = sorted(set(Order.objects.filter(order_number=order_number).values_list('deadline', flat=True)))
        for order_date in order_dates:
            completion_date = {
                    "date": (order_date - timedelta(days=params.production_lag)).strftime("%Y-%m-%d") if order_date else None,
                    "plates": [
                        {
                            "count": order.count,
                            "length": order.product.length,
                            "width": order.product.width,
                            "height": order.product.height,
                            "class": order.product.concrete_class,
                            "wire_bottom": order.product.wire_bottom,
                            "wire_top": order.product.wire_top,
                            "name": order.product.name
                        }
                        for order in Order.objects.filter(order_number=order_number, deadline=order_date)
                    ]
                }
            order_data["completion_dates"].append(completion_date)
        orders_data.append(order_data)
    return {
        "directory": {
            "concrete_classes": unit_plate_prices,
            "wire": {
                "price": unit_wire_price
            },
            "retooling": {
                "price": unit_retooling_price
            },
            "track": {
                "length": params.road_length
            },
            "tail_len": params.tail_length,
            "force_tail": params.force_tail
        },
        "ready_plates": [
            {
                "count": inv.count,
                "name": inv.product.name,
                "length": inv.product.length,
                "width": inv.product.width,
                "height": inv.product.height,
                "class": inv.product.concrete_class,
                "wire_bottom": inv.product.wire_bottom,
                "wire_top": inv.product.wire_top
            } for inv in inventory
        ],
        "available_tracks": available_tracks,
        "orders": orders_data
    }


def calculate_plan(date_from, date_to):
    params = Parameters.get_solo()
    # Получаем данные из API
    headers = {'api-key': '12345678'}
    payload = json.dumps(prepare_data(date_from, date_to), ensure_ascii=False, cls=DecimalEncoder)
    with open('output.json', 'w', encoding='utf-8') as f:
        f.write(payload)
    url = 'http://api:8080/api/v1/calculate/default/'
    r = requests.post(url, headers=headers, data=payload)
    r.raise_for_status()
    data = r.json()

    with open('response.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, cls=DecimalEncoder))

    # Сначала создаем RetoolingInfo и DailyRetoolings
    retooling_data = data.get('retooling_info', {})
    daily_retoolings = []

    for daily_data in retooling_data.get('daily_retoolings', []):
        daily_retooling = DailyRetooling.objects.create(
            date=datetime.strptime(daily_data['date'], '%Y-%m-%d').date(),
            count=daily_data['count'],
            price=daily_data['price'],
        )
        for changes in daily_data.get('changes', []):
            daily_retooling.changes.create(
                from_width=changes['from']['width'],
                from_height=changes['from']['height'],
                to_width=changes['to']['width'],
                to_height=changes['to']['height'],
            )
        daily_retoolings.append(daily_retooling)

    retooling_info = RetoolingInfo.objects.create(
        price=retooling_data.get('price', 0),
        last_state_width=retooling_data.get('last_state', {}).get('width', 0),
        last_state_height=retooling_data.get('last_state', {}).get('height', 0),
    )
    retooling_info.daily_retoolings.set(daily_retoolings)

    # Теперь создаем ProductionPlan с привязкой retooling_info
    production_plan = ProductionPlan.objects.create(retooling_info=retooling_info)

    # Обрабатываем дни производства
    for day_data in data.get('plan', []):
        if params.road_length == day_data['free_len']:
            continue
        production_day = ProductionDay.objects.create(
            date=datetime.strptime(day_data['day'], '%Y-%m-%d').date(),
            height=day_data['height'],
            width=day_data['width'],
            useful_len=day_data['useful_len'],
            free_len=day_data['free_len'],
            concrete_class=day_data['concrete_class'],
            wire_bottom=day_data['wire_bottom'],
            wire_top=day_data['wire_top'],
            total_cost=day_data['total_cost'],
            free_cost=day_data['free_cost'],
            full_cost=day_data['full_cost'],
        )

        # Добавляем плиты для этого дня
        prev_plate = None
        for i, plate_data in enumerate(day_data.get('plates', [])):
            if prev_plate and (
                        prev_plate.order == plate_data['order']
                    and prev_plate.name == plate_data['name']
                    and prev_plate.length == plate_data['length']
                    and prev_plate.width == plate_data['width']
                    and prev_plate.height == plate_data['height']
                    and prev_plate.concrete_class == plate_data['class']
                    and prev_plate.wire_bottom == plate_data['wire_bottom']
                    and prev_plate.wire_top == plate_data['wire_top']
                ):
                prev_plate.count += 1
                prev_plate.save()
                continue
            else:
                prev_plate = ProductionDayPlate.objects.create(
                    production_day=production_day,
                    name=plate_data['name'],
                    count=1,
                    length=plate_data['length'],
                    width=plate_data['width'],
                    height=plate_data['height'],
                    order=plate_data['order'],
                    concrete_class=plate_data['class'],
                    wire_bottom=plate_data['wire_bottom'],
                    wire_top=plate_data['wire_top'],
                )

        production_plan.plan.add(production_day)

    # Обрабатываем использованные готовые плиты
    for plate_data in data.get('used_ready_plates', []):
        used_plate = UsedReadyPlate.objects.create(
            name=plate_data['name'],
            count=plate_data['count'],
            length=plate_data['length'],
            width=plate_data['width'],
            height=plate_data['height'],
            order=plate_data['order'],
            concrete_class=plate_data['class'],
            wire_bottom=plate_data['wire_bottom'],
            wire_top=plate_data['wire_top'],
        )
        production_plan.used_ready_plates.add(used_plate)

    # Обрабатываем неразмещенные плиты
    prev_plate = None
    for unplace_data in data.get('unplaced_plates', []):
        for plate_data in unplace_data['plate']:
            if prev_plate and (
                prev_plate.order == plate_data['order']
                and prev_plate.name == plate_data['name']
                and prev_plate.length == plate_data['length']
                and prev_plate.width == plate_data['width']
                and prev_plate.height == plate_data['height']
                and prev_plate.concrete_class == plate_data['class']
                and prev_plate.wire_bottom == plate_data['wire_bottom']
                and prev_plate.wire_top == plate_data['wire_top']
            ):
                prev_plate.count += 1
                prev_plate.save()
                continue
            else:
                prev_plate = UnplacedPlate.objects.create(
                    name=plate_data['name'],
                    count=plate_data['count'],
                    length=plate_data['length'],
                    width=plate_data['width'],
                    height=plate_data['height'],
                    order=plate_data.get('order'),
                    concrete_class=plate_data['class'],
                    wire_bottom=plate_data['wire_bottom'],
                    wire_top=plate_data['wire_top'],
                )

    # Обрабатываем оставшиеся готовые плиты
    for plate_data in data.get('left_ready_plates', []):
        left_plate = LeftReadyPlate.objects.create(
            name=plate_data['name'],
            count=plate_data['count'],
            length=plate_data['length'],
            width=plate_data['width'],
            height=plate_data['height'],
            order=plate_data.get('order'),
            concrete_class=plate_data['class'],
            wire_bottom=plate_data['wire_bottom'],
            wire_top=plate_data['wire_top'],
        )
        production_plan.left_ready_plates.add(left_plate)
