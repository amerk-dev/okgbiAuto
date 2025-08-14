import json
import os
from datetime import datetime, timedelta

import requests
from django.db import transaction

from calculation.models import ReadyPlate, Order, Plate, Parameters, Deadline

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
            order = Order.objects.create(
                order_number=order_data['number'].strip(),
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
        # data = json.loads(s)
        ready_plates = data['ready_plates']
        orders = data['orders']

        with transaction.atomic():
            ReadyPlate.objects.all().delete()
            Order.objects.all().delete()

            self._process_ready_plates(ready_plates)
            self._process_orders(orders)

s = '''{
	"ready_plates": [],
	"orders": [
		{
			"number": "ТПК03763   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-15T00:00:00",
					"plates": [
						{
							"name": "ПБ 58-15 8 нагрузка",
							"count": 2,
							"length": 5780,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 20,
							"wire_top": 4
						},
						{
							"name": "ПБ 28-10 8 нагрузка",
							"count": 1,
							"length": 2780,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 4
						},
						{
							"name": "ПБ 28-12 8 нагрузка",
							"count": 1,
							"length": 2780,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 2
						},
						{
							"name": "ПБ 58-12 8 нагрузка",
							"count": 4,
							"length": 5780,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						},
						{
							"name": "ПБ 58-10 8 нагрузка",
							"count": 2,
							"length": 5780,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 14,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК38777   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПБ 70-10 8 нагрузка",
							"count": 4,
							"length": 6980,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 20,
							"wire_top": 4
						},
						{
							"name": "ПБ 60-10 8 нагрузка",
							"count": 8,
							"length": 5980,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 14,
							"wire_top": 4
						},
						{
							"name": "ПБ 60-15 8 нагрузка",
							"count": 32,
							"length": 5980,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 20,
							"wire_top": 4
						},
						{
							"name": "ПБ 37-15 8 нагрузка",
							"count": 20,
							"length": 3680,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 32-15 8 нагрузка",
							"count": 27,
							"length": 3180,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 75-10 8 нагрузка",
							"count": 2,
							"length": 7480,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 28,
							"wire_top": 4
						},
						{
							"name": "ПБ 37-10 8 нагрузка",
							"count": 13,
							"length": 3680,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 32-10 8 нагрузка",
							"count": 19,
							"length": 3180,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 75-15 8 нагрузка",
							"count": 38,
							"length": 7480,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 32,
							"wire_top": 4
						},
						{
							"name": "ПБ 74-15 8 нагрузка",
							"count": 38,
							"length": 7380,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 32,
							"wire_top": 4
						},
						{
							"name": "ПБ 65-12 8 нагрузка",
							"count": 91,
							"length": 6480,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 18,
							"wire_top": 4
						},
						{
							"name": "ПБ 70-12 8 нагрузка",
							"count": 24,
							"length": 6980,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 22,
							"wire_top": 4
						},
						{
							"name": "ПБ 70-15 8 нагрузка",
							"count": 48,
							"length": 6980,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 28,
							"wire_top": 4
						},
						{
							"name": "ПБ 37-12 8 нагрузка",
							"count": 2,
							"length": 3680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 65-15 8 нагрузка",
							"count": 58,
							"length": 6480,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 24,
							"wire_top": 4
						},
						{
							"name": "ПБ 74-10 8 нагрузка",
							"count": 7,
							"length": 7380,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 28,
							"wire_top": 4
						},
						{
							"name": "ПБ 74-12 8 нагрузка",
							"count": 26,
							"length": 7380,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 26,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК39054   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-07-11T00:00:00",
					"plates": [
						{
							"name": "ПБ 48-15 8 нагрузка",
							"count": 2,
							"length": 4780,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40085   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-05T00:00:00",
					"plates": [
						{
							"name": "ПБ 45-15 8 нагрузка",
							"count": 2,
							"length": 4480,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40175   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-15T00:00:00",
					"plates": [
						{
							"name": "ПБ 3300-12 8 нагрузка",
							"count": 2,
							"length": 3280,
							"width": 1195,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 4960-15 8 нагрузка",
							"count": 10,
							"length": 4960,
							"width": 1495,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 4430-12 8 нагрузка",
							"count": 2,
							"length": 4430,
							"width": 1195,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 4430-10 8 нагрузка",
							"count": 1,
							"length": 4430,
							"width": 995,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						}
					]
				}
			]
		},
		{
			"number": "ТПК40199   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-12T00:00:00",
					"plates": [
						{
							"name": "ПНО 58-12 (3.1 ПБ 58-12) 8 нагрузка",
							"count": 2,
							"length": 5780,
							"width": 1195,
							"height": 160,
							"class": "В30",
							"wire_bottom": 26,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40232   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПБ 48-12 8 нагрузка",
							"count": 2,
							"length": 4780,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 57-12 8 нагрузка",
							"count": 4,
							"length": 5680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						},
						{
							"name": "ПБ 42-15 8 нагрузка",
							"count": 2,
							"length": 4180,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 42-12 8 нагрузка",
							"count": 2,
							"length": 4180,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 54-15 8 нагрузка",
							"count": 1,
							"length": 5380,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						},
						{
							"name": "ПБ 66-15 8 нагрузка",
							"count": 2,
							"length": 6580,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 24,
							"wire_top": 4
						},
						{
							"name": "ПБ 54-12 8 нагрузка",
							"count": 2,
							"length": 5380,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 4
						},
						{
							"name": "ПБ 27-15 8 нагрузка",
							"count": 3,
							"length": 2680,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						},
						{
							"name": "ПБ 36-15 8 нагрузка",
							"count": 1,
							"length": 3580,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 57-15 8 нагрузка",
							"count": 1,
							"length": 5680,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 20,
							"wire_top": 4
						},
						{
							"name": "ПБ 36-12 8 нагрузка",
							"count": 4,
							"length": 3580,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						},
						{
							"name": "ПБ 27-12 8 нагрузка",
							"count": 3,
							"length": 2680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40240   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-20T00:00:00",
					"plates": [
						{
							"name": "ПБ 44-12 8 нагрузка",
							"count": 6,
							"length": 4380,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 33-10 8 нагрузка",
							"count": 4,
							"length": 3280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 43-10 8 нагрузка",
							"count": 3,
							"length": 4280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 4
						},
						{
							"name": "ПБ 43-12 8 нагрузка",
							"count": 3,
							"length": 4280,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40257   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-12T00:00:00",
					"plates": [
						{
							"name": "ПБ 70-12 8 нагрузка",
							"count": 2,
							"length": 6980,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 22,
							"wire_top": 4
						},
						{
							"name": "ПБ 24-15 8 нагрузка",
							"count": 1,
							"length": 2380,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40267   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-15T00:00:00",
					"plates": [
						{
							"name": "ПБ 4800-12 8 нагрузка",
							"count": 17,
							"length": 4800,
							"width": 1195,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						}
					]
				}
			]
		},
		{
			"number": "ТПК40301   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПБ 64-12 8 нагрузка",
							"count": 1,
							"length": 6380,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 18,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40316   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-13T00:00:00",
					"plates": [
						{
							"name": "ПНО 40-15 (3.1 ПБ 40-15) 8 нагрузка",
							"count": 4,
							"length": 3980,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 6
						}
					]
				}
			]
		},
		{
			"number": "ТПК40406   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-14T00:00:00",
					"plates": [
						{
							"name": "ПБ 57-12 10 нагрузка",
							"count": 4,
							"length": 5680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 18,
							"wire_top": 4
						},
						{
							"name": "ПБ 57-10 10 нагрузка",
							"count": 1,
							"length": 5680,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40432   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-15T00:00:00",
					"plates": [
						{
							"name": "ПБ 22-15 8 нагрузка",
							"count": 1,
							"length": 2180,
							"width": 1495,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 53-15 8 нагрузка",
							"count": 7,
							"length": 5280,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40478   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-14T00:00:00",
					"plates": [
						{
							"name": "ПНО 39-12 (3.1 ПБ 39-12) 6 нагрузка",
							"count": 16,
							"length": 3880,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40502   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-19T00:00:00",
					"plates": [
						{
							"name": "ПБ 75-10 8 нагрузка",
							"count": 1,
							"length": 7480,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 28,
							"wire_top": 4
						},
						{
							"name": "ПБ 81-10 8 нагрузка",
							"count": 1,
							"length": 8080,
							"width": 995,
							"height": 220,
							"class": "В30",
							"wire_bottom": 32,
							"wire_top": 4
						},
						{
							"name": "ПБ 39-12 8 нагрузка",
							"count": 1,
							"length": 3880,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 32-12 8 нагрузка",
							"count": 2,
							"length": 3180,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						},
						{
							"name": "ПБ 75-12 8 нагрузка",
							"count": 1,
							"length": 7480,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 26,
							"wire_top": 4
						},
						{
							"name": "ПБ 57-12 8 нагрузка",
							"count": 14,
							"length": 5680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40514   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-18T00:00:00",
					"plates": [
						{
							"name": "ПБ 57-12 8 нагрузка",
							"count": 6,
							"length": 5680,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40551   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-18T00:00:00",
					"plates": [
						{
							"name": "ПНО 24-12 (3.1 ПБ 24-12) 6 нагрузка",
							"count": 24,
							"length": 2380,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40555   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-18T00:00:00",
					"plates": [
						{
							"name": "ПБ 35-10 8 нагрузка",
							"count": 1,
							"length": 3480,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 35-15 8 нагрузка",
							"count": 1,
							"length": 3480,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 39-15 8 нагрузка",
							"count": 6,
							"length": 3880,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 45-15 8 нагрузка",
							"count": 3,
							"length": 4480,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 2
						},
						{
							"name": "ПБ 45-12 8 нагрузка",
							"count": 2,
							"length": 4480,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40556   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-18T00:00:00",
					"plates": [
						{
							"name": "ПНО 55-15 (3.1 ПБ 55-15) 6 нагрузка",
							"count": 5,
							"length": 5480,
							"width": 1495,
							"height": 160,
							"class": "В30",
							"wire_bottom": 24,
							"wire_top": 6
						},
						{
							"name": "ПНО 46-15 (3.1 ПБ 46-15) 6 нагрузка",
							"count": 2,
							"length": 4580,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 18,
							"wire_top": 6
						},
						{
							"name": "ПНО 32-15 (3.1 ПБ 32-15) 6 нагрузка",
							"count": 2,
							"length": 3180,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 6
						},
						{
							"name": "ПНО 25-12 (3.1 ПБ 25-12) 6 нагрузка",
							"count": 1,
							"length": 2480,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 4
						},
						{
							"name": "ПНО 50-12 (3.1 ПБ 50-12) 6 нагрузка",
							"count": 1,
							"length": 4980,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 14,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40562   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-08T00:00:00",
					"plates": [
						{
							"name": "ПБ 6160-15 8 нагрузка",
							"count": 1,
							"length": 6160,
							"width": 1495,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						}
					]
				}
			]
		},
		{
			"number": "ТПК40566   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-18T00:00:00",
					"plates": [
						{
							"name": "ПБ 23-15 8 нагрузка",
							"count": 1,
							"length": 2280,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						},
						{
							"name": "ПБ 23-10 8 нагрузка",
							"count": 2,
							"length": 2280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 2
						},
						{
							"name": "ПБ 43-10 8 нагрузка",
							"count": 2,
							"length": 4280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 4
						},
						{
							"name": "ПБ 48-15 8 нагрузка",
							"count": 7,
							"length": 4780,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 2
						},
						{
							"name": "ПБ 43-15 8 нагрузка",
							"count": 5,
							"length": 4280,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40569   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-25T00:00:00",
					"plates": [
						{
							"name": "ПБ 52-12 8 нагрузка",
							"count": 30,
							"length": 5180,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 4
						},
						{
							"name": "ПБ 52-15 8 нагрузка",
							"count": 66,
							"length": 5180,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40570   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-19T00:00:00",
					"plates": [
						{
							"name": "ПБ 3600-10 8 нагрузка",
							"count": 1,
							"length": 3600,
							"width": 995,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 5800-15 8 нагрузка",
							"count": 5,
							"length": 5800,
							"width": 1495,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 4600-12 8 нагрузка",
							"count": 5,
							"length": 4600,
							"width": 1195,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПБ 4600-15 8 нагрузка",
							"count": 2,
							"length": 4600,
							"width": 1495,
							"height": 220,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						}
					]
				}
			]
		},
		{
			"number": "ТПК40578   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-27T00:00:00",
					"plates": [
						{
							"name": "ПНО 40-12 (3.1 ПБ 40-12) 8 нагрузка",
							"count": 6,
							"length": 4180,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 4
						},
						{
							"name": "ПНО 30-15 (3.1 ПБ 30-15) 8 нагрузка",
							"count": 15,
							"length": 2980,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 6
						},
						{
							"name": "ПНО 16-12 (3.1 ПБ 16-12) 8 нагрузка",
							"count": 1,
							"length": 1580,
							"width": 1195,
							"height": 160,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПНО 24-15 (3.1 ПБ 24-15) 8 нагрузка",
							"count": 8,
							"length": 2380,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 6
						}
					]
				}
			]
		},
		{
			"number": "ТПК40589   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-22T00:00:00",
					"plates": [
						{
							"name": "ПНО 38-12 (3.1 ПБ 38-12) 8 нагрузка",
							"count": 8,
							"length": 3780,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 4
						},
						{
							"name": "ПНО 45-15 (3.1 ПБ 45-15) 8 нагрузка",
							"count": 2,
							"length": 4480,
							"width": 1495,
							"height": 160,
							"class": "В30",
							"wire_bottom": 18,
							"wire_top": 6
						},
						{
							"name": "ПНО 45-12 (3.1 ПБ 45-12) 8 нагрузка",
							"count": 5,
							"length": 4480,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 14,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40596   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-27T00:00:00",
					"plates": [
						{
							"name": "ПНО 6500-12 (3.1 ПБ 6500-12) 6 нагрузка",
							"count": 4,
							"length": 6500,
							"width": 1195,
							"height": 160,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						},
						{
							"name": "ПНО 6500-15 (3.1 ПБ 6500-15) 6 нагрузка",
							"count": 3,
							"length": 6500,
							"width": 1495,
							"height": 160,
							"class": 0,
							"wire_bottom": 0,
							"wire_top": 0
						}
					]
				}
			]
		},
		{
			"number": "ТПК40603   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-19T00:00:00",
					"plates": [
						{
							"name": "ПБ 33-12 8 нагрузка",
							"count": 1,
							"length": 3280,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40617   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПБ 43-10 8 нагрузка",
							"count": 3,
							"length": 4280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 4
						},
						{
							"name": "ПБ 40-10 8 нагрузка",
							"count": 1,
							"length": 3980,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 43-12 8 нагрузка",
							"count": 5,
							"length": 4280,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 40-12 8 нагрузка",
							"count": 2,
							"length": 3980,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40623   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-20T00:00:00",
					"plates": [
						{
							"name": "ПБ 40-12 8 нагрузка",
							"count": 2,
							"length": 3980,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 50-15 8 нагрузка",
							"count": 3,
							"length": 4980,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 16,
							"wire_top": 4
						},
						{
							"name": "ПБ 40-15 8 нагрузка",
							"count": 1,
							"length": 3980,
							"width": 1495,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						},
						{
							"name": "ПБ 46-12 8 нагрузка",
							"count": 7,
							"length": 4580,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 2
						}
					]
				}
			]
		},
		{
			"number": "ТПК40624   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПНО 41-12 (3.1 ПБ 41-12) 8 нагрузка",
							"count": 4,
							"length": 4080,
							"width": 1195,
							"height": 160,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 4
						},
						{
							"name": "ПНО 41-15 (3.1 ПБ 41-15) 8 нагрузка",
							"count": 7,
							"length": 4080,
							"width": 1495,
							"height": 160,
							"class": "В25",
							"wire_bottom": 12,
							"wire_top": 6
						}
					]
				}
			]
		},
		{
			"number": "ТПК40665   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "2025-09-19T00:00:00",
					"plates": [
						{
							"name": "ПБ 36-12 8 нагрузка",
							"count": 6,
							"length": 3580,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 2
						},
						{
							"name": "ПБ 38-12 8 нагрузка",
							"count": 6,
							"length": 3780,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 8,
							"wire_top": 2
						},
						{
							"name": "ПБ 36-10 8 нагрузка",
							"count": 1,
							"length": 3580,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 38-10 8 нагрузка",
							"count": 1,
							"length": 3780,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 33-10 8 нагрузка",
							"count": 1,
							"length": 3280,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 6,
							"wire_top": 4
						},
						{
							"name": "ПБ 21-12 8 нагрузка",
							"count": 4,
							"length": 2080,
							"width": 1195,
							"height": 220,
							"class": "В25",
							"wire_bottom": 4,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40720   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПБ 41-10 12,5 нагрузка",
							"count": 6,
							"length": 4080,
							"width": 995,
							"height": 220,
							"class": "В25",
							"wire_bottom": 10,
							"wire_top": 4
						}
					]
				}
			]
		},
		{
			"number": "ТПК40722   ",
			"production_days": 0,
			"completion_dates": [
				{
					"date": "0001-01-01T00:00:00",
					"plates": [
						{
							"name": "ПНО 74-15 (3.1 ПБ 74-15) 4,5 нагрузка",
							"count": 1,
							"length": 7380,
							"width": 1495,
							"height": 160,
							"class": "В35",
							"wire_bottom": 42,
							"wire_top": 6
						},
						{
							"name": "ПНО 74-12 (3.1 ПБ 74-12) 6 нагрузка",
							"count": 4,
							"length": 7380,
							"width": 1195,
							"height": 160,
							"class": "В35",
							"wire_bottom": 40,
							"wire_top": 4
						}
					]
				}
			]
		}
	]
}'''