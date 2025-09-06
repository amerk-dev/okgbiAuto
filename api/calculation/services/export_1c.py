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
    url = params.url_1c_export
    headers = {'Authorization': 'Basic V2ViVXNlcjo3ODk0NTYxMjMw', 'Content-Type': 'application/json'}

    # Получаем сегодняшнюю дату
    today = datetime.date.today()
    errors = []

    today_tracks = Track.objects.filter(day=today).order_by('position')
    for position, track in enumerate(today_tracks, 1):
        if not track.plates.exists():
            continue
        export_1c = Export1c.objects.get_or_create(date=today, track_position=position)[0]
        plates_data = {}
        for plate in track.plates.all():
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
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "number": export_1c.document_number or "",
            "plates": list(plates_data.values()),
            'comment': f'Дорожка {position}'
        }

        # json.dump(export_data, open(f'{export_data["date"]}_{track.position+1}_export_1c.json', 'w'), indent=2, ensure_ascii=False)
        # Отправляем данные в 1С
        try:
            response = requests.post(url, headers=headers, json=export_data)
            response.raise_for_status()
            response = response.json()
            if response.get('number'):
                export_1c.document_number = response['number']
                export_1c.save()
            if response.get('error'):
                errors.append(response['error'])
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'Ошибка при отправке данных в 1С: {str(e)}'}
    if errors:
        return {'status': 'error', 'message': 'Ошибки при отправке данных в 1С: ' + ', '.join(errors)}
    return {'status': 'success', 'message': 'Данные успешно выгружены в 1С'}
