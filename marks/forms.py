from django import forms

from .models import Marks


class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ['student', 'subject', 'exam_type', 'marks', 'max_marks', 'exam_date']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select', 'id': 'id_marks_student'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_marks_subject', 'autocomplete': 'off'}),
            'exam_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_marks_exam_type'}),
            'marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_marks_obtained',
                'min': 0,
                'autocomplete': 'off',
                'placeholder': 'e.g. 75',
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_marks_maximum',
                'min': 1,
                'autocomplete': 'off',
                'placeholder': 'e.g. 100',
            }),
            'exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'id_marks_exam_date', 'autocomplete': 'off'}),
        }

    def clean_marks(self):
        marks = self.cleaned_data.get('marks')
        if marks is not None and marks < 0:
            raise forms.ValidationError('Marks cannot be negative.')
        return marks

    def clean_max_marks(self):
        max_marks = self.cleaned_data.get('max_marks')
        if max_marks is not None and max_marks < 1:
            raise forms.ValidationError('Maximum marks must be at least 1.')
        return max_marks

    def clean(self):
        cleaned = super().clean()
        marks = cleaned.get('marks')
        max_marks = cleaned.get('max_marks')
        if marks is not None and max_marks is not None and marks > max_marks:
            self.add_error('marks', f'Marks obtained ({marks}) cannot exceed maximum marks ({max_marks}).')
        return cleaned
