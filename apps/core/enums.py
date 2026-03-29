from django.db import models


class Status(models.TextChoices):
    ACTIVE = "active", "Active"
    SOLD = "sold", "Sold"
    ARCHIVED = "archived", "Archived"


class OfferStatus(models.TextChoices):
    PENDING = 'pending', 'В ожидании'
    ACCEPTED = 'accepted', 'Принято'
    REJECTED = 'rejected', 'Отклонено'
