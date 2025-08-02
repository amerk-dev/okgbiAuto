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

    Track.recreate_tracks()