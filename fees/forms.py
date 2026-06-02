from django import forms

from students.models import Student

from .models import FeePayment, FeeStructure, StudentFee


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model  = FeeStructure
        fields = ['department', 'year', 'category', 'period',
                  'amount', 'academic_year', 'due_date', 'description']
        widgets = {
            'department':    forms.TextInput(attrs={'class': 'form-control'}),
            'year':          forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4}),
            'category':      forms.Select(attrs={'class': 'form-select'}),
            'period':        forms.Select(attrs={'class': 'form-select'}),
            'amount':        forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-26'}),
            'due_date':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class StudentFeeForm(forms.ModelForm):
    class Meta:
        model  = StudentFee
        fields = ['student', 'fee_structure', 'amount_due', 'amount_paid', 'due_date', 'remarks']
        widgets = {
            'student':       forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'amount_due':    forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'amount_paid':   forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
            'due_date':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        paid = cleaned.get('amount_paid')
        due  = cleaned.get('amount_due')
        if paid is not None and due is not None and paid > due:
            self.add_error('amount_paid', 'Amount paid cannot exceed amount due.')
        return cleaned


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model  = FeePayment
        fields = ['amount', 'payment_date', 'mode', 'reference_no', 'notes']
        widgets = {
            'amount':       forms.NumberInput(attrs={'class': 'form-control', 'min': 0.01, 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode':         forms.Select(attrs={'class': 'form-select'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID / DD / Cheque No'}),
            'notes':        forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class FeeFilterForm(forms.Form):
    """Faculty filter form for the fee list page."""
    student    = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label='All Students',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    category   = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + FeeStructure.FEE_CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status     = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + StudentFee.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
    )
    year       = forms.IntegerField(
        required=False,
        min_value=1, max_value=4,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
    )
    academic_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-26'}),
    )
