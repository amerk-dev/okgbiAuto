from django.db import models


class CalculationStatus(models.Model):
    """
    Model to track the status of calculation tasks.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # Progress in percentage (0-100)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Calculation Status'
        verbose_name_plural = 'Calculation Statuses'
        ordering = ['-created_at']

    def __str__(self):
        return f"Calculation {self.task_id} - {self.status}"