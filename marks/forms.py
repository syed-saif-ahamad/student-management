from django import forms

from .models import Marks


class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ['student', 'subject', 'exam_type', 'marks', 'max_marks', 'exam_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        marks = cleaned.get('marks')
        max_marks = cleaned.get('max_marks')
        if marks is not None and max_marks is not None and marks > max_marks:
            self.add_error('marks', 'Marks cannot exceed maximum marks.')
        return cleaned
