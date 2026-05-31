from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile',
    )
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    year = models.IntegerField()
    phone = models.CharField(max_length=15)
    joining_date = models.DateField()

    class Meta:
        ordering = ['roll_no']

    def __str__(self):
        return f'{self.name} ({self.roll_no})'
