from datetime import datetime, timedelta

import requests
from django.db import transaction

from calculation.models import Inventory, Order, Product, Parameters


def update_data():
    params = Parameters.get_solo()
    url = params.url_1c
    headers = {'sign': params.sign_1c,}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response = response.json()
    ready_plates = response['ready_plates']
    orders = response['orders']

    with transaction.atomic():
        Product.objects.all().delete()
        Inventory.objects.all().delete()
        Order.objects.all().delete()

        for ready_plate in ready_plates:
            product, _ = Product.objects.get_or_create(
                name=ready_plate['name'],
                length=ready_plate['length'],
                width=ready_plate['width'],
                height=ready_plate['height'],
                concrete_class=ready_plate['class'] or 'В25',
                wire_bottom=ready_plate['wire_bottom'],
                wire_top=ready_plate['wire_top'],
            )
            Inventory.objects.create(
                product=product,
                count=max(ready_plate['count'], 1), #TODO: tmp fix
            )

        for order_data in orders:
            for completion_date in order_data['completion_dates']:
                plates = completion_date['plates']
                for plate in plates:
                    product, _ = Product.objects.get_or_create(
                        name=plate['name'],
                        length=plate['length'],
                        width=plate['width'],
                        height=plate['height'],
                        concrete_class=plate['class'] or 'В25',
                        wire_bottom=plate['wire_bottom'],
                        wire_top=plate['wire_top'],
                    )

                    if completion_date['date'] == '0001-01-01T00:00:00':
                        deadline_date = None
                    else:
                        deadline_date = datetime.strptime(completion_date['date'], '%Y-%m-%dT%H:%M:%S').date()

                    Order.objects.create(
                        order_number=order_data['number'].strip(),
                        deadline=deadline_date,
                        count=plate['count'],
                        product=product,
                    )
