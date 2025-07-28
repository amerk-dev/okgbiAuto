from django.conf import settings
from django.db import models
from django.utils import timezone


class ErrorLog(models.Model):
    """Model for tracking errors in the application"""
    ERROR_SOURCES = [
        ('api', 'API'),
        ('1c', '1C'),
        ('calculation', 'Расчет'),
        ('view', 'Представление'),
        ('other', 'Другое'),
    ]

    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    source = models.CharField(max_length=255)
    traceback = models.TextField()
    details = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Лог ошибок'
        verbose_name_plural = 'Логи ошибок'

    def __str__(self):
        return f"{self.error_type}: {self.error_message[:50]}"

    @property
    def short_error(self):
        return f"{self.error_message[:100]}{'...' if len(self.error_message) > 100 else ''}"


class ErrorReport(models.Model):
    """Model for storing user reports of errors"""
    error_log = models.ForeignKey(
        ErrorLog,
        on_delete=models.CASCADE,
        related_name='user_reports'
    )
    user_description = models.TextField()
    contact_info = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Отчет об ошибке'
        verbose_name_plural = 'Отчеты об ошибках'

    def __str__(self):
        return f"Report for {self.error_log.id} - {self.timestamp}"
