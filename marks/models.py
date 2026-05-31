from django.db import models

from students.models import Student


class Marks(models.Model):
    EXAM_INTERNAL = 'Internal'
    EXAM_ASSIGNMENT = 'Assignment'
    EXAM_MIDTERM = 'Midterm'
    EXAM_FINAL = 'Final'

    EXAM_TYPE_CHOICES = [
        (EXAM_INTERNAL, 'Internal'),
        (EXAM_ASSIGNMENT, 'Assignment'),
        (EXAM_MIDTERM, 'Midterm'),
        (EXAM_FINAL, 'Final'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks_records')
    subject = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES)
    marks = models.IntegerField()
    max_marks = models.IntegerField()
    exam_date = models.DateField()

    class Meta:
        ordering = ['-exam_date']
        verbose_name_plural = 'Marks'

    def __str__(self):
        return f'{self.student.roll_no} - {self.subject} - {self.marks}/{self.max_marks}'

    @property
    def percentage(self):
        if self.max_marks == 0:
            return 0
        return round((self.marks / self.max_marks) * 100, 2)
