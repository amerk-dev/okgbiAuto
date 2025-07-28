import datetime
import json

import requests
from django.conf import settings

from calculation.models import Parameters


def export_to_1c():
    """
    Экспортирует данные о выполненных за день работах в 1С
    """
    params = Parameters.get_solo()
    url = params.url_1c
    headers = {'sign': params.sign_1c, 'Content-Type': 'application/json'}
    
    # Получаем сегодняшнюю дату
    today = datetime.date.today()
    
    # Получаем все дорожки на сегодня
    production_days = ProductionDay.objects.filter(date=today)
    
    # Формируем данные для отправки
    export_data = {
        'date': today.strftime('%Y-%m-%d'),
        'tracks': []
    }
    
    # Добавляем информацию о каждой дорожке
    for track in production_days:
        track_data = {
            'id': track.id,
            'width': track.width,
            'height': track.height,
            'concrete_class': track.concrete_class,
            'wire_top': track.wire_top,
            'wire_bottom': track.wire_bottom,
            'useful_len': track.useful_len,
            'free_len': track.free_len,
            'total_cost': float(track.total_cost),
            'plates': []
        }
        
        # Добавляем информацию о плитах на дорожке
        for plate in track.plates.all():
            plate_data = {
                'id': plate.id,
                'name': plate.name,
                'count': plate.count,
                'length': plate.length,
                'width': plate.width,
                'height': plate.height,
                'order': plate.order,
                'concrete_class': plate.concrete_class,
                'wire_bottom': plate.wire_bottom,
                'wire_top': plate.wire_top
            }
            track_data['plates'].append(plate_data)
        
        export_data['tracks'].append(track_data)
    
    # Отправляем данные в 1С
    try:
        response = requests.post(url, headers=headers, json=export_data)
        response.raise_for_status()
        return {'status': 'success', 'message': 'Данные успешно выгружены в 1С'}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f'Ошибка при отправке данных в 1С: {str(e)}'}