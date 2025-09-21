from celery import shared_task
from django.db import transaction

from .models import CalculationStatus
from .services.calculator.calculate import calculate_plan
from .services.manage_1c import Update1CDataCommand


@shared_task(bind=True)
def calculate_task(self):
    """
    Celery task to run the calculation process.
    """
    # Create or update the calculation status
    status, created = CalculationStatus.objects.get_or_create(
        task_id=self.request.id,
        defaults={
            'status': 'pending',
            'progress': 0,
            'message': 'Calculation task created'
        }
    )

    def update_status(progress, message, status_value=None):
        status.progress = progress
        status.message = message
        if status_value:
            status.status = status_value
        status.save(update_fields=['progress', 'message', 'status'])

    try:
        # Update status to in_progress
        update_status(10, 'Подготовка', 'in_progress')

        # Update data from 1C (can be in transaction if needed)
        update_status(20, 'Обновление данных из 1c')
        Update1CDataCommand().execute()

        # Calculate plan (can also be in transaction if needed)
        update_status(30, 'Расчет плана')
        calculate_plan(update_status)

        # Update status to completed
        update_status(100, 'Расчет завершен успешно', 'completed')

        return {'status': 'success', 'message': 'Расчет завершен успешно'}

    except Exception as e:
        # Update status to failed
        update_status(100, f'Вычисление не удалось: {str(e)}', 'failed')

        # Re-raise the exception to mark the task as failed
        raise