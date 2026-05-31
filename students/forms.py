from django import forms

from .models import Student


class StudentForm(forms.ModelForm):
    create_login = forms.BooleanField(
        required=False,
        initial=True,
        label='Create login account for student',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Login password'}),
        help_text='Required when creating a login account.',
    )

    class Meta:
        model = Student
        fields = [
            'roll_no', 'name', 'email', 'department',
            'year', 'phone', 'joining_date',
        ]
        widgets = {
            'roll_no': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('create_login') and not cleaned.get('password'):
            self.add_error('password', 'Password is required when creating a login account.')
        return cleaned


class StudentSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, roll no, or email...',
        }),
    )
