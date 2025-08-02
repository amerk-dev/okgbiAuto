from django.apps import AppConfig


class CalculationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calculation'
    verbose_name = 'Настройки'

    def ready(self):
        # Import signals to register them
        import calculation.signals
