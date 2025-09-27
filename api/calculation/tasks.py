from celery import shared_task
from django.db import transaction
import json

from .models import CalculationStatus, Customer, Order, Deadline, Plate, ReadyPlate, Parameters, UnitPrice, Track
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


@shared_task(bind=True)
def calculate_algorithm_demo(self, file_content):
    """
    Celery task to run the algorithm demonstration with uploaded data.
    """
    # Create or update the calculation status
    status, created = CalculationStatus.objects.get_or_create(
        task_id=self.request.id,
        defaults={
            'status': 'pending',
            'progress': 0,
            'message': 'Algorithm demo task created'
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
        update_status(50, 'Расчет...', 'in_progress')

        # Parse the uploaded JSON file
        data = json.loads(file_content)

        # Start a transaction to create a temporary database state
        with transaction.atomic():
            # Create a savepoint to be able to rollback
            sid = transaction.savepoint()
            Plate.all_objects.all().delete()
            Order.objects.all().delete()
            Track.objects.update(customer=None)

            update_status(20, 'Обработка данных')

            # Copy parameters and unit prices from the main database
            params = Parameters.get_solo()
            unit_prices = UnitPrice.objects.all()

            # Process the data and create necessary objects
            # Create customers, orders, deadlines, and plates
            customers = {}
            for order_data in data.get('orders', []):
                # Create or get customer
                customer_name = order_data.get('customer', 'Unknown')
                if customer_name not in customers:
                    customer, _ = Customer.objects.get_or_create(name=customer_name)
                    customers[customer_name] = customer
                else:
                    customer = customers[customer_name]

                # Create order
                order = Order.objects.create(
                    customer=customer,
                    order_number=order_data.get('number', 'Unknown')
                )

                # Process completion dates
                for completion_date in order_data.get('completion_dates', []):
                    date_str = completion_date.get('date')
                    if date_str:
                        import datetime
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').date()
                        deadline = Deadline.objects.create(
                            order=order,
                            date=date_obj
                        )

                        # Process plates
                        for plate_data in completion_date.get('plates', []):
                            for _ in range(plate_data.get('count', 1)):
                                Plate.objects.create(
                                    name=plate_data.get('name', 'Unknown'),
                                    length=plate_data.get('length', 0),
                                    width=plate_data.get('width', 0),
                                    height=plate_data.get('height', 0),
                                    concrete_class=plate_data.get('class', 'B25'),
                                    wire_bottom=plate_data.get('wire_bottom', 0),
                                    wire_top=plate_data.get('wire_top', 0),
                                    deadline=deadline
                                )

            # Process ready plates
            for ready_plate_data in data.get('ready_plates', []):
                ReadyPlate.objects.create(
                    name=ready_plate_data.get('name', 'Unknown'),
                    length=ready_plate_data.get('length', 0),
                    width=ready_plate_data.get('width', 0),
                    height=ready_plate_data.get('height', 0),
                    concrete_class=ready_plate_data.get('class', 'B25'),
                    wire_bottom=ready_plate_data.get('wire_bottom', 0),
                    wire_top=ready_plate_data.get('wire_top', 0)
                )

            update_status(50, 'Запуск расчета')

            # Run the calculation
            calculate_plan(update_status)

            update_status(90, 'Подготовка результатов')

            # Get the results in a format similar to the main frontend
            tracks = Track.objects.all().order_by('day', 'position')

            # Group tracks by position
            positions = {}
            for track in tracks:
                if track.position not in positions:
                    positions[track.position] = []
                positions[track.position].append(track)

            result = []

            for pos, pos_tracks in positions.items():
                first_track = pos_tracks[0]

                track_data = {
                    "id": first_track.id,
                    "name": f"Дорожка {pos + 1}",
                    "contractor": first_track.customer.name if first_track.customer else "",
                    "days": [],
                }

                # Group by date
                days = {}
                for t in pos_tracks:
                    day_str = t.day.strftime('%Y-%m-%d')
                    if day_str not in days:
                        days[day_str] = {
                            "date": day_str,
                            "plates": []
                        }

                    # Add plates for this track and day
                    for plate in t.plates.all():
                        plate_data = {
                            "id": plate.id,
                            "name": plate.name,
                            "clean_name": plate.clean_name,
                            "length": plate.length,
                            "width": plate.width,
                            "height": plate.height,
                            "concrete_class": plate.concrete_class,
                            "wire_top": plate.wire_top,
                            "wire_bottom": plate.wire_bottom,
                            "deadline": plate.deadline.date.strftime('%Y-%m-%d') if plate.deadline.date else None,
                            "order": plate.deadline.order.order_number if plate.deadline else None,
                            "customer": plate.deadline.order.customer.name if plate.deadline and plate.deadline.order.customer else None,
                        }
                        days[day_str]["plates"].append(plate_data)

                # Sort days and add to track
                track_data["days"] = [days[d] for d in sorted(days.keys())]
                result.append(track_data)

            # Rollback the transaction to clean up the database
            transaction.savepoint_rollback(sid)

        # Update status to completed
        update_status(100, 'Демонстрация завершена успешно', 'completed')

        return {'status': 'success', 'result': result}

    except Exception as e:
        # Update status to failed
        update_status(100, f'Демонстрация не удалась: {str(e)}', 'failed')

        # Re-raise the exception to mark the task as failed
        raise
