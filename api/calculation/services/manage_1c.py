import json
import os
from datetime import datetime, timedelta

import requests
from django.db import transaction

from calculation.models import ReadyPlate, Order, Plate, Parameters, Deadline, Customer


class Update1CDataCommand:
    def __init__(self):
        self.params = Parameters.get_solo()

    def _fetch_data(self):
        url = self.params.url_1c
        headers = {'Authorization': 'Basic V2ViVXNlcjo3ODk0NTYxMjMw',}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _process_ready_plates(self, ready_plates):
        plates = []
        for plate in ready_plates:
            for _ in range(max(plate['count'], 1)):
                plates.append(ReadyPlate(
                    name=plate['name'],
                    length=plate['length'],
                    width=plate['width'],
                    height=plate['height'],
                    concrete_class=plate['class'] or 'В25',
                    wire_bottom=plate['wire_bottom'],
                    wire_top=plate['wire_top'],
                ))
        ReadyPlate.objects.bulk_create(plates)

    def _process_orders(self, orders):
        for order_data in orders:
            cust = None
            if order_data.get('kontragent'):
                cust, _ = Customer.objects.get_or_create(name=order_data['kontragent'])

            order = Order.objects.create(
                order_number=order_data['number'].strip(),
                customer=cust,
                # TODO: После получения информации о структуре Контрагента, добавить его создание
            )
            for completion_date in order_data['completion_dates']:

                if completion_date['date'] == '0001-01-01T00:00:00':
                    deadline_date = None
                else:
                    deadline_date = datetime.strptime(completion_date['date'], '%Y-%m-%dT%H:%M:%S').date()
                deadline = Deadline.objects.create(
                    order=order,
                    date=deadline_date,
                )
                plates = completion_date['plates']

                plates_to_create = []
                for plate_data in plates:
                    for _ in range(plate_data['count']):
                        plate = Plate(
                                        name=plate_data['name'],
                                        length=plate_data['length'],
                                        width=plate_data['width'],
                                        height=plate_data['height'],
                                        concrete_class=plate_data['class'] or 'В25',
                                        wire_bottom=plate_data['wire_bottom'],
                                        wire_top=plate_data['wire_top'],
                                        deadline=deadline
                                    )
                        plates_to_create.append(plate)
                Plate.objects.bulk_create(plates_to_create)

    def execute(self):
        data = self._fetch_data()
        ready_plates = data['ready_plates']
        orders = data['orders']
        with transaction.atomic():
            ReadyPlate.all_objects.all().delete()
            Order.objects.all().delete()
            self._process_ready_plates(ready_plates)
            self._process_orders(orders)
            Customer.objects.filter(order__isnull=True).delete()

