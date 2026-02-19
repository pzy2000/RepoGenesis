from django.db import models
from django.contrib.auth.models import User


class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="movies")

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"

from django.db import models

# Create your models here.
