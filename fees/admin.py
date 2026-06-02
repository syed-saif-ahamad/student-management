from django.contrib import admin

from .models import FeePayment, FeeStructure, StudentFee


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display  = ['department', 'year', 'category', 'period', 'amount', 'academic_year', 'due_date']
    list_filter   = ['category', 'period', 'academic_year']
    search_fields = ['department']


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display  = ['student', 'fee_structure', 'amount_due', 'amount_paid', 'status', 'due_date']
    list_filter   = ['status', 'fee_structure__category']
    search_fields = ['student__name', 'student__roll_no']
    readonly_fields = ['updated_at', 'created_at']


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display  = ['student_fee', 'amount', 'payment_date', 'mode', 'reference_no', 'received_by']
    list_filter   = ['mode', 'payment_date']
    search_fields = ['student_fee__student__name', 'reference_no']
    readonly_fields = ['created_at']
