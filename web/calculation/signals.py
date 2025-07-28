import datetime

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='calculation.Parameters')
def update_tracks_on_parameters_change(sender, instance, created, **kwargs):
    """
    Signal handler to update tracks when Parameters are saved.
    This replaces the logic that was previously in Parameters.save method.
    """
    # Import Track inside the function to avoid circular imports
    from calculation.models.base import Track

    weekend_settings = [
        (0, 'monday_weekend'),
        (1, 'tuesday_weekend'),
        (2, 'wednesday_weekend'),
        (3, 'thursday_weekend'),
        (4, 'friday_weekend'),
        (5, 'saturday_weekend'),
        (6, 'sunday_weekend')
    ]

    with transaction.atomic():
        days = 100
        Track.objects.all().delete()

        new_tracks = []
        for day_step in range(days):
            day = datetime.date.today() + datetime.timedelta(days=day_step)

            # Проверяем, является ли день выходным
            is_weekend = any(
                day.weekday() == day_num and getattr(instance, day_attr)
                for day_num, day_attr in weekend_settings
            )

            if is_weekend:
                continue
            for position in range(instance.default_available_tracks):
                new_tracks.append(Track(
                    day=day,
                    position=position
                ))
        Track.objects.bulk_create(new_tracks)