import json
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import faculty_required, student_required
from students.models import Student

from .forms import FeeFilterForm, FeePaymentForm, FeeStructureForm, StudentFeeForm
from .models import FeePayment, FeeStructure, StudentFee


# ─────────────────────────────────────────────────────────────────────────────
# Faculty views — full CRUD
# ─────────────────────────────────────────────────────────────────────────────

@faculty_required
def fee_dashboard(request):
    """Faculty overview: totals, pending fees, recent payments."""
    total_due  = StudentFee.objects.aggregate(s=Sum('amount_due'))['s']  or Decimal('0')
    total_paid = StudentFee.objects.aggregate(s=Sum('amount_paid'))['s'] or Decimal('0')
    total_bal  = total_due - total_paid

    pending_count  = StudentFee.objects.filter(status=StudentFee.STATUS_PENDING).count()
    partial_count  = StudentFee.objects.filter(status=StudentFee.STATUS_PARTIAL).count()
    paid_count     = StudentFee.objects.filter(status=StudentFee.STATUS_PAID).count()

    recent_payments = (
        FeePayment.objects
        .select_related('student_fee__student', 'received_by')
        .order_by('-payment_date')[:10]
    )
    overdue_fees = (
        StudentFee.objects
        .select_related('student', 'fee_structure')
        .exclude(status=StudentFee.STATUS_PAID)
        .exclude(status=StudentFee.STATUS_WAIVED)
        .order_by('due_date')[:10]
    )

    return render(request, 'fees/fee_dashboard.html', {
        'total_due':      total_due,
        'total_paid':     total_paid,
        'total_bal':      total_bal,
        'pending_count':  pending_count,
        'partial_count':  partial_count,
        'paid_count':     paid_count,
        'recent_payments': recent_payments,
        'overdue_fees':   overdue_fees,
    })


@faculty_required
def fee_list(request):
    """Full fee list with search & filter."""
    form    = FeeFilterForm(request.GET or None)
    records = StudentFee.objects.select_related('student', 'fee_structure').all()

    if form.is_valid():
        if form.cleaned_data.get('student'):
            records = records.filter(student=form.cleaned_data['student'])
        if form.cleaned_data.get('category'):
            records = records.filter(fee_structure__category=form.cleaned_data['category'])
        if form.cleaned_data.get('status'):
            records = records.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('department'):
            records = records.filter(student__department__icontains=form.cleaned_data['department'])
        if form.cleaned_data.get('year'):
            records = records.filter(student__year=form.cleaned_data['year'])
        if form.cleaned_data.get('academic_year'):
            records = records.filter(fee_structure__academic_year=form.cleaned_data['academic_year'])

    # search by roll no or name
    q = request.GET.get('q', '').strip()
    if q:
        records = records.filter(
            Q(student__name__icontains=q) | Q(student__roll_no__icontains=q)
        )

    total_due  = records.aggregate(s=Sum('amount_due'))['s']  or Decimal('0')
    total_paid = records.aggregate(s=Sum('amount_paid'))['s'] or Decimal('0')

    return render(request, 'fees/fee_list.html', {
        'records':    records,
        'form':       form,
        'q':          q,
        'total_due':  total_due,
        'total_paid': total_paid,
        'total_bal':  total_due - total_paid,
    })


@faculty_required
def fee_structure_list(request):
    structures = FeeStructure.objects.all()
    dept   = request.GET.get('department', '')
    year   = request.GET.get('year', '')
    ay     = request.GET.get('academic_year', '')
    if dept:
        structures = structures.filter(department__icontains=dept)
    if year:
        structures = structures.filter(year=year)
    if ay:
        structures = structures.filter(academic_year=ay)

    departments   = FeeStructure.objects.values_list('department', flat=True).distinct()
    academic_years = FeeStructure.objects.values_list('academic_year', flat=True).distinct()

    return render(request, 'fees/fee_structure_list.html', {
        'structures':    structures,
        'departments':   departments,
        'academic_years': academic_years,
        'f_dept': dept, 'f_year': year, 'f_ay': ay,
    })


@faculty_required
def fee_structure_create(request):
    form = FeeStructureForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.created_by = request.user
        obj.save()
        messages.success(request, f'Fee structure created: {obj}')
        return redirect('fees:structure_list')
    return render(request, 'fees/fee_structure_form.html', {'form': form, 'title': 'Add Fee Structure'})


@faculty_required
def fee_structure_edit(request, pk):
    obj  = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fee structure updated.')
        return redirect('fees:structure_list')
    return render(request, 'fees/fee_structure_form.html', {'form': form, 'title': 'Edit Fee Structure', 'obj': obj})


@faculty_required
def fee_structure_delete(request, pk):
    obj = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Fee structure deleted.')
        return redirect('fees:structure_list')
    return render(request, 'fees/fee_confirm_delete.html', {'obj': obj, 'type': 'structure'})


@faculty_required
def student_fee_create(request):
    form = StudentFeeForm(request.POST or None)
    has_structures = FeeStructure.objects.exists()
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.updated_by = request.user
        obj.save()
        messages.success(request, f'Fee record created for {obj.student.name}.')
        return redirect('fees:list')
    return render(request, 'fees/student_fee_form.html', {
        'form': form,
        'title': 'Add Fee Record',
        'has_structures': has_structures,
        'structure_data': json.dumps(form.structure_data),
    })


@faculty_required
def student_fee_edit(request, pk):
    obj  = get_object_or_404(StudentFee, pk=pk)
    form = StudentFeeForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated.updated_by = request.user
        updated.save()
        messages.success(request, 'Fee record updated.')
        return redirect('fees:list')
    return render(request, 'fees/student_fee_form.html', {
        'form': form,
        'title': 'Edit Fee Record',
        'obj': obj,
        'has_structures': True,
        'structure_data': json.dumps(form.structure_data),
    })


@faculty_required
def student_fee_delete(request, pk):
    obj = get_object_or_404(StudentFee, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Fee record deleted.')
        return redirect('fees:list')
    return render(request, 'fees/fee_confirm_delete.html', {'obj': obj, 'type': 'fee'})


@faculty_required
def student_fee_detail(request, pk):
    """Faculty view of one student's complete fee + payment history."""
    fee_record = get_object_or_404(StudentFee.objects.select_related('student', 'fee_structure'), pk=pk)
    payments   = fee_record.payments.select_related('received_by').order_by('-payment_date')
    return render(request, 'fees/student_fee_detail.html', {
        'fee_record': fee_record,
        'payments':   payments,
    })


@faculty_required
def add_payment(request, fee_pk):
    fee_record = get_object_or_404(StudentFee, pk=fee_pk)
    form = FeePaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        payment = form.save(commit=False)
        payment.student_fee = fee_record
        payment.received_by = request.user
        payment.save()

        # update the parent StudentFee amount_paid
        total_paid = fee_record.payments.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        fee_record.amount_paid = total_paid
        fee_record.updated_by = request.user
        fee_record.save()  # save() auto-recomputes status

        messages.success(request, f'Payment of ₹{payment.amount} recorded.')
        return redirect('fees:detail', pk=fee_pk)
    return render(request, 'fees/add_payment.html', {
        'form':       form,
        'fee_record': fee_record,
    })


@faculty_required
def fee_student_summary(request, student_pk):
    """Faculty view: all fee records for one student."""
    student = get_object_or_404(Student, pk=student_pk)
    return _student_fee_summary_view(request, student, is_faculty_view=True)


# ─────────────────────────────────────────────────────────────────────────────
# Student view — read-only
# ─────────────────────────────────────────────────────────────────────────────

@student_required
def my_fees(request):
    """Student view: read-only summary of own fees."""
    if request.method != 'GET':
        return HttpResponseForbidden('Students cannot modify fee records.')
    student = get_object_or_404(Student, user=request.user)
    return _student_fee_summary_view(request, student, is_faculty_view=False)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helper
# ─────────────────────────────────────────────────────────────────────────────

def _student_fee_summary_view(request, student, is_faculty_view):
    fee_records = (
        StudentFee.objects
        .filter(student=student)
        .select_related('fee_structure')
        .order_by('fee_structure__category', 'due_date')
    )

    # Per-category breakdown
    categories = {}
    for rec in fee_records:
        cat = rec.fee_structure.get_category_display()
        categories.setdefault(cat, []).append(rec)

    total_due  = fee_records.aggregate(s=Sum('amount_due'))['s']  or Decimal('0')
    total_paid = fee_records.aggregate(s=Sum('amount_paid'))['s'] or Decimal('0')
    total_bal  = total_due - total_paid

    # Payment history (all payments across all fee records)
    all_payments = (
        FeePayment.objects
        .filter(student_fee__student=student)
        .select_related('student_fee__fee_structure', 'received_by')
        .order_by('-payment_date')
    )

    template = 'fees/my_fees.html' if not is_faculty_view else 'fees/faculty_student_fees.html'
    return render(request, template, {
        'student':      student,
        'fee_records':  fee_records,
        'categories':   categories,
        'total_due':    total_due,
        'total_paid':   total_paid,
        'total_bal':    total_bal,
        'all_payments': all_payments,
        'is_faculty':   is_faculty_view,
    })
