from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import faculty_required, student_required
from students.models import Student

from .forms import AttendanceForm, BulkAttendanceDateForm
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
    date_filter = request.GET.get('date')
    dept_filter = request.GET.get('department')

    if student_id:
        records = records.filter(student_id=student_id)
    if date_filter:
        records = records.filter(date=date_filter)
    if dept_filter:
        records = records.filter(student__department=dept_filter)

    students = Student.objects.all()
    departments = Student.objects.values_list('department', flat=True).distinct().order_by('department')

    return render(request, 'attendance/attendance_list.html', {
        'records': records,
        'students': students,
        'departments': departments,
        'selected_student': student_id,
        'selected_date': date_filter,
        'selected_department': dept_filter,
    })


@faculty_required
def attendance_by_date(request):
    """
    Dedicated date-view: faculty picks a date and sees every student's
    attendance for that day — including students with no record yet.
    Shows Present / Absent / Late counts and per-department breakdown.
    """
    selected_date = request.GET.get('date', '')
    dept_filter   = request.GET.get('department', '')

    # All distinct dates that have records — used to populate a "jump to date" list
    available_dates = (
        Attendance.objects
        .values_list('date', flat=True)
        .distinct()
        .order_by('-date')
    )

    departments = (
        Student.objects
        .values_list('department', flat=True)
        .distinct()
        .order_by('department')
    )

    rows = []
    stats = {'present': 0, 'absent': 0, 'late': 0, 'total': 0, 'no_record': 0}
    dept_stats = {}           # {dept: {present, absent, late, total}}

    if selected_date:
        students_qs = Student.objects.all().order_by('department', 'roll_no')
        if dept_filter:
            students_qs = students_qs.filter(department=dept_filter)

        # Fetch all attendance for the selected date in one DB hit
        att_map = {
            rec.student_id: rec
            for rec in Attendance.objects.filter(date=selected_date, student__in=students_qs)
        }

        for student in students_qs:
            rec = att_map.get(student.pk)
            status = rec.status if rec else None
            rows.append({
                'student': student,
                'record':  rec,
                'status':  status,
            })

            # aggregate stats
            stats['total'] += 1
            dept = student.department
            dept_stats.setdefault(dept, {'present': 0, 'absent': 0, 'late': 0, 'total': 0})
            dept_stats[dept]['total'] += 1

            if status == Attendance.STATUS_PRESENT:
                stats['present'] += 1
                dept_stats[dept]['present'] += 1
            elif status == Attendance.STATUS_ABSENT:
                stats['absent'] += 1
                dept_stats[dept]['absent'] += 1
            elif status == Attendance.STATUS_LATE:
                stats['late'] += 1
                dept_stats[dept]['late'] += 1
            else:
                stats['no_record'] += 1

        # attendance % for the day (present+late / students with a record)
        marked = stats['present'] + stats['absent'] + stats['late']
        stats['attendance_pct'] = (
            round((stats['present'] + stats['late']) / marked * 100, 1) if marked else 0
        )

    return render(request, 'attendance/attendance_by_date.html', {
        'rows':            rows,
        'stats':           stats,
        'dept_stats':      dept_stats,
        'selected_date':   selected_date,
        'dept_filter':     dept_filter,
        'available_dates': available_dates,
        'departments':     departments,
    })


@faculty_required
def bulk_attendance(request):
    """
    Single-page bulk attendance marking.
    GET with no params  → show date/department picker.
    GET with ?date=...  → show all students for that date with current status pre-filled.
    POST                → save all statuses and redirect to list.
    """
    departments = list(
        Student.objects.values_list('department', flat=True).distinct().order_by('department')
    )

    selected_date = request.GET.get('date') or request.POST.get('date')
    selected_dept = request.GET.get('department') or request.POST.get('department')

    date_form = BulkAttendanceDateForm(
        request.GET if request.method == 'GET' and selected_date else None,
        departments=departments,
        initial={'date': timezone.localdate(), 'department': selected_dept or ''},
    )

    # ── POST: save all rows ──────────────────────────────────────────────────
    if request.method == 'POST':
        att_date_str = request.POST.get('date')
        if not att_date_str:
            messages.error(request, 'No date supplied.')
            return redirect('attendance:bulk')

        try:
            from datetime import datetime
            att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('attendance:bulk')

        students_qs = Student.objects.all().order_by('roll_no')
        if selected_dept:
            students_qs = students_qs.filter(department=selected_dept)

        saved = 0
        for student in students_qs:
            field_name = f'status_{student.pk}'
            status_value = request.POST.get(field_name)
            if status_value not in [Attendance.STATUS_PRESENT,
                                    Attendance.STATUS_ABSENT,
                                    Attendance.STATUS_LATE]:
                continue

            obj, created = Attendance.objects.get_or_create(
                student=student,
                date=att_date,
                defaults={'status': status_value},
            )
            if not created and obj.status != status_value:
                obj.status = status_value
                obj.save()
            saved += 1

        messages.success(request, f'Attendance saved for {saved} student(s) on {att_date_str}.')
        return redirect('attendance:list')

    # ── GET: show the marking form ───────────────────────────────────────────
    student_rows = []
    if selected_date:
        students_qs = Student.objects.all().order_by('roll_no')
        if selected_dept:
            students_qs = students_qs.filter(department=selected_dept)

        existing = {
            rec.student_id: rec.status
            for rec in Attendance.objects.filter(date=selected_date, student__in=students_qs)
        }

        for student in students_qs:
            student_rows.append({
                'student': student,
                'current_status': existing.get(student.pk, Attendance.STATUS_PRESENT),
            })

    return render(request, 'attendance/bulk_attendance.html', {
        'date_form': date_form,
        'student_rows': student_rows,
        'selected_date': selected_date,
        'selected_dept': selected_dept,
        'status_choices': Attendance.STATUS_CHOICES,
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
        'record': record,
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
    """Read-only view — students can only VIEW their own attendance."""
    student = get_object_or_404(Student, user=request.user)
    records = Attendance.objects.filter(student=student).order_by('-date')
    percentage = calculate_attendance_percentage(student)

    monthly = {}
    for rec in records:
        key = rec.date.strftime('%B %Y')
        monthly.setdefault(key, {'present': 0, 'absent': 0, 'late': 0, 'total': 0})
        monthly[key]['total'] += 1
        if rec.status == Attendance.STATUS_PRESENT:
            monthly[key]['present'] += 1
        elif rec.status == Attendance.STATUS_ABSENT:
            monthly[key]['absent'] += 1
        elif rec.status == Attendance.STATUS_LATE:
            monthly[key]['late'] += 1

    return render(request, 'attendance/my_attendance.html', {
        'records': records,
        'percentage': percentage,
        'student': student,
        'monthly': monthly,
    })
