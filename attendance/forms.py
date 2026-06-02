from django import forms
from django.utils import timezone

from students.models import Student

from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkAttendanceDateForm(forms.Form):
    """Step 1 – faculty picks the date to mark attendance for."""
    date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Attendance Date',
    )
    department = forms.ChoiceField(
        required=False,
        choices=[],          # populated dynamically in the view
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Filter by Department (optional)',
    )

    def __init__(self, *args, **kwargs):
        departments = kwargs.pop('departments', [])
        super().__init__(*args, **kwargs)
        dept_choices = [('', 'All Departments')] + [(d, d) for d in departments]
        self.fields['department'].choices = dept_choices
