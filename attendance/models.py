from django.db import models

from students.models import Student


class Attendance(models.Model):
    STATUS_PRESENT = 'Present'
    STATUS_ABSENT = 'Absent'
    STATUS_LATE = 'Late'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'date']

    def __str__(self):
        return f'{self.student.roll_no} - {self.date} - {self.status}'
