from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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

    student    = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks_records')
    subject    = models.CharField(max_length=100)
    exam_type  = models.CharField(max_length=50, choices=EXAM_TYPE_CHOICES)
    marks      = models.IntegerField()
    max_marks  = models.IntegerField()
    exam_date  = models.DateField()

    # Audit tracking fields ─────────────────────────────────────────────────
    created_by   = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='marks_created',
    )
    updated_by   = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='marks_updated',
    )
    created_at   = models.DateTimeField(default=timezone.now)
    updated_at   = models.DateTimeField(auto_now=True)

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


class MarksAuditLog(models.Model):
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
    ]

    marks       = models.ForeignKey(
        Marks, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
    )
    action      = models.CharField(max_length=10, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='marks_audit_logs',
    )
    timestamp   = models.DateTimeField(default=timezone.now)

    # Snapshot of the record at the time of the action
    student_name  = models.CharField(max_length=150)
    roll_no       = models.CharField(max_length=20)
    subject       = models.CharField(max_length=100)
    exam_type     = models.CharField(max_length=50)
    marks_value   = models.IntegerField(null=True, blank=True)
    max_marks_value = models.IntegerField(null=True, blank=True)
    exam_date     = models.DateField(null=True, blank=True)
    changes       = models.TextField(blank=True)   # human-readable diff for updates

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Marks Audit Log'
        verbose_name_plural = 'Marks Audit Logs'

    def __str__(self):
        return f'{self.action} — {self.subject} ({self.roll_no}) by {self.performed_by} @ {self.timestamp:%Y-%m-%d %H:%M}'
