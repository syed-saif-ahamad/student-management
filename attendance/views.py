from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import faculty_required, student_required
from students.models import Student

from .forms import AttendanceForm
from .models import Attendance


def calculate_attendance_percentage(student):
    records = Attendance.objects.filter(student=student)
    total = records.count()
    if total == 0:
        return 0
    present = records.filter(
        status__in=[Attendance.STATUS_PRESENT, Attendance.STATUS_LATE]
    ).count()
    return round((present / total) * 100, 2)


@faculty_required
def attendance_list(request):
    records = Attendance.objects.select_related('student').all()
    student_id = request.GET.get('student')
    if student_id:
        records = records.filter(student_id=student_id)
    students = Student.objects.all()
    return render(request, 'attendance/attendance_list.html', {
        'records': records,
        'students': students,
        'selected_student': student_id,
    })


@faculty_required
def attendance_create(request):
    form = AttendanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance marked successfully.')
        return redirect('attendance:list')
    return render(request, 'attendance/attendance_form.html', {
        'form': form,
        'title': 'Mark Attendance',
    })


@faculty_required
def attendance_update(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    form = AttendanceForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Attendance updated successfully.')
        return redirect('attendance:list')
    return render(request, 'attendance/attendance_form.html', {
        'form': form,
        'title': 'Edit Attendance',
    })


@faculty_required
def attendance_delete(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Attendance record deleted.')
        return redirect('attendance:list')
    return render(request, 'attendance/attendance_confirm_delete.html', {'record': record})


@student_required
def my_attendance(request):
    student = get_object_or_404(Student, user=request.user)
    records = Attendance.objects.filter(student=student)
    percentage = calculate_attendance_percentage(student)
    return render(request, 'attendance/my_attendance.html', {
        'records': records,
        'percentage': percentage,
        'student': student,
    })
