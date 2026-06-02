from django import forms
from django.utils import timezone

from students.models import Student

from .models import FeePayment, FeeStructure, StudentFee


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model  = FeeStructure
        fields = ['department', 'year', 'category', 'period',
                  'amount', 'academic_year', 'due_date', 'description']
        widgets = {
            'department':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'year':          forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 4, 'placeholder': '1–4'}),
            'category':      forms.Select(attrs={'class': 'form-select'}),
            'period':        forms.Select(attrs={'class': 'form-select'}),
            'amount':        forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-26'}),
            'due_date':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set today as default for due_date on blank form
        if not self.instance.pk and not self.data.get('due_date'):
            self.fields['due_date'].initial = timezone.localdate()


class StudentFeeForm(forms.ModelForm):
    """
    Faculty form to assign a fee record to a student.
    The fee_structure dropdown filters to only show existing structures.
    amount_due and due_date are auto-filled by JS when a structure is selected,
    but can be overridden manually.
    """

    class Meta:
        model  = StudentFee
        fields = ['student', 'fee_structure', 'amount_due', 'amount_paid', 'due_date', 'remarks']
        widgets = {
            'student':       forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select', 'id': 'id_fee_structure'}),
            'amount_due':    forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'step': '0.01',
                'placeholder': '0.00', 'id': 'id_amount_due',
            }),
            'amount_paid':   forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0, 'step': '0.01',
                'placeholder': '0.00', 'id': 'id_amount_paid',
            }),
            'due_date':      forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date', 'id': 'id_due_date',
            }),
            'remarks':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set amount_paid default to 0 on new records
        if not self.instance.pk:
            self.fields['amount_paid'].initial = 0
        # Build a data map for JS auto-fill: {structure_id: {amount, due_date}}
        self.structure_data = {
            str(s.pk): {'amount': str(s.amount), 'due_date': str(s.due_date)}
            for s in FeeStructure.objects.all()
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
            'amount':       forms.NumberInput(attrs={'class': 'form-control', 'min': 0.01, 'step': '0.01', 'placeholder': '0.00'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode':         forms.Select(attrs={'class': 'form-select'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction ID / DD / Cheque No (optional)'}),
            'notes':        forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.data.get('payment_date'):
            self.fields['payment_date'].initial = timezone.localdate()


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
