from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from students.models import Student


class FeeStructure(models.Model):
    """
    Defines how much each fee category costs for a given
    department + year combination.  Faculty create these once;
    individual student fee records are derived from them.
    """
    FEE_TUITION     = 'Tuition'
    FEE_UNIVERSITY  = 'University'
    FEE_TRANSPORT   = 'Transport'
    FEE_EXAMINATION = 'Examination'
    FEE_LIBRARY     = 'Library'
    FEE_LABORATORY  = 'Laboratory'
    FEE_HOSTEL      = 'Hostel'
    FEE_MISC        = 'Miscellaneous'

    FEE_CATEGORY_CHOICES = [
        (FEE_TUITION,     'Tuition Fee'),
        (FEE_UNIVERSITY,  'University Fee'),
        (FEE_TRANSPORT,   'Bus / Transport Fee'),
        (FEE_EXAMINATION, 'Examination Fee'),
        (FEE_LIBRARY,     'Library Fee'),
        (FEE_LABORATORY,  'Laboratory Fee'),
        (FEE_HOSTEL,      'Hostel Fee'),
        (FEE_MISC,        'Miscellaneous'),
    ]

    SEMESTER_1 = 'Sem 1'
    SEMESTER_2 = 'Sem 2'
    ANNUAL     = 'Annual'

    PERIOD_CHOICES = [
        (SEMESTER_1, 'Semester 1'),
        (SEMESTER_2, 'Semester 2'),
        (ANNUAL,     'Annual'),
    ]

    department   = models.CharField(max_length=100)
    year         = models.IntegerField()
    category     = models.CharField(max_length=20, choices=FEE_CATEGORY_CHOICES)
    period       = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=ANNUAL)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    academic_year = models.CharField(max_length=10, default='2025-26',
                                     help_text='e.g. 2025-26')
    due_date     = models.DateField()
    description  = models.TextField(blank=True)
    created_by   = models.ForeignKey(User, null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='fee_structures_created')
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['department', 'year', 'category']
        unique_together = ['department', 'year', 'category', 'period', 'academic_year']
        verbose_name = 'Fee Structure'

    def __str__(self):
        return f'{self.department} Yr{self.year} — {self.category} ({self.academic_year})'


class StudentFee(models.Model):
    """
    Per-student fee record for one category.
    Created/updated by faculty; read-only for students.
    """
    STATUS_PAID     = 'Paid'
    STATUS_PARTIAL  = 'Partially Paid'
    STATUS_PENDING  = 'Pending'
    STATUS_WAIVED   = 'Waived'

    STATUS_CHOICES = [
        (STATUS_PAID,    'Paid'),
        (STATUS_PARTIAL, 'Partially Paid'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_WAIVED,  'Waived'),
    ]

    student       = models.ForeignKey(Student, on_delete=models.CASCADE,
                                      related_name='fee_records')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE,
                                      related_name='student_fees')
    amount_due    = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date      = models.DateField()
    status        = models.CharField(max_length=15, choices=STATUS_CHOICES,
                                     default=STATUS_PENDING)
    remarks       = models.TextField(blank=True)
    updated_by    = models.ForeignKey(User, null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='fees_updated')
    updated_at    = models.DateTimeField(auto_now=True)
    created_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['due_date', 'fee_structure__category']
        unique_together = ['student', 'fee_structure']
        verbose_name = 'Student Fee'

    def __str__(self):
        return (f'{self.student.roll_no} — '
                f'{self.fee_structure.category} — {self.status}')

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def save(self, *args, **kwargs):
        # Auto-compute status from amounts
        if self.amount_paid <= 0:
            self.status = self.STATUS_PENDING
        elif self.amount_paid >= self.amount_due:
            self.status = self.STATUS_PAID
        else:
            self.status = self.STATUS_PARTIAL
        super().save(*args, **kwargs)


class FeePayment(models.Model):
    """
    Individual payment instalment for a StudentFee record.
    Provides full payment history.
    """
    MODE_CASH   = 'Cash'
    MODE_ONLINE = 'Online'
    MODE_DD     = 'Demand Draft'
    MODE_CHEQUE = 'Cheque'
    MODE_UPI    = 'UPI'

    MODE_CHOICES = [
        (MODE_CASH,   'Cash'),
        (MODE_ONLINE, 'Online Transfer'),
        (MODE_DD,     'Demand Draft'),
        (MODE_CHEQUE, 'Cheque'),
        (MODE_UPI,    'UPI'),
    ]

    student_fee    = models.ForeignKey(StudentFee, on_delete=models.CASCADE,
                                       related_name='payments')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date   = models.DateField(default=timezone.localdate)
    mode           = models.CharField(max_length=15, choices=MODE_CHOICES,
                                      default=MODE_CASH)
    reference_no   = models.CharField(max_length=100, blank=True,
                                      help_text='Transaction ID / DD No / Cheque No')
    received_by    = models.ForeignKey(User, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='payments_received')
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Fee Payment'

    def __str__(self):
        return (f'{self.student_fee.student.roll_no} — '
                f'₹{self.amount} on {self.payment_date}')
