import datetime
import json

import requests
from django.conf import settings

from calculation.models import Parameters

from calculation.models import Export1c

from calculation.models import Plate, Track


def export_to_1c():
    """
    Экспортирует данные о выполненных за день работах в 1С
    """
    params = Parameters.get_solo()
    url = params.url_1c
    headers = {'sign': params.sign_1c, 'Content-Type': 'application/json'}

    # Получаем сегодняшнюю дату
    today = datetime.date.today()
    export_1c = Export1c.objects.get_or_create(date=today)[0]

    today_tracks_ids = Track.objects.filter(day=today).values_list('id', flat=True)
    plates = Plate.objects.filter(track_id__in=today_tracks_ids).prefetch_related('deadline__order')

    plates_data = {}
    for plate in plates:
        key = (plate.name, plate.deadline.order.order_number)
        if key in plates_data:
            plates_data[key]['count'] += 1
        else:
            plates_data[key] = {
                'name': plate.name,
                'count': 1,
                'OrderNumber': plate.deadline.order.order_number,
            }


    # Формируем данные для отправки
    export_data = {
        "OPZS": [
            {
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "number": export_1c.document_number or "",
                "plates": list(plates_data.values()),
            }
        ]
    }

    print(json.dump(export_data, open('test_export_1c.json', 'w'), indent=2, ensure_ascii=False))

    # Отправляем данные в 1С
    try:
    #     response = requests.post(url, headers=headers, json=export_data)
    #     response.raise_for_status()
    #     response = response.json()
    #     export_1c.document_number = response['OPZS'][0]['number']
    #     export_1c.save()
        return {'status': 'success', 'message': 'Данные успешно выгружены в 1С'}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f'Ошибка при отправке данных в 1С: {str(e)}'}
