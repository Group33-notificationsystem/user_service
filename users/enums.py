# users/enums.py
from django.db import models

class NotificationStatus(models.TextChoices):
    DELIVERED = "delivered", "Delivered"
    PENDING = "pending", "Pending" 
    FAILED = "failed", "Failed"

class NotificationType(models.TextChoices):
    EMAIL = "email", "Email"
    PUSH = "push", "Push"