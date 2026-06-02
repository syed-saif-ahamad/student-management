from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import faculty_required
from attendance.models import Attendance
from attendance.views import calculate_attendance_percentage
from marks.models import Marks

from .forms import StudentForm, StudentSearchForm
from .models import Student


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _student_stats(student, pass_threshold):
    """Return a dict of computed stats for one student."""
    marks_qs = Marks.objects.filter(student=student)
    total_marks = marks_qs.aggregate(s=Sum('marks'))['s'] or 0
    total_max   = marks_qs.aggregate(s=Sum('max_marks'))['s'] or 0
    overall_pct = round((total_marks / total_max) * 100, 1) if total_max else None

    # Backlog: any subject+exam_type whose % < pass_threshold
    backlogs = []
    for rec in marks_qs:
        if rec.max_marks and (rec.marks / rec.max_marks * 100) < pass_threshold:
            backlogs.append(f'{rec.subject} ({rec.exam_type})')

    att_pct = calculate_attendance_percentage(student)

    return {
        'student':      student,
        'overall_pct':  overall_pct,
        'total_marks':  total_marks,
        'total_max':    total_max,
        'backlogs':     backlogs,
        'backlog_count': len(backlogs),
        'has_backlog':  len(backlogs) > 0,
        'att_pct':      att_pct,
    }


# ──────────────────────────────────────────────────────────────
# CRUD views (unchanged)
# ──────────────────────────────────────────────────────────────

@faculty_required
def student_list(request):
    form = StudentSearchForm(request.GET or None)
    students = Student.objects.all()
    if form.is_valid() and form.cleaned_data.get('q'):
        q = form.cleaned_data['q']
        students = students.filter(
            Q(name__icontains=q) | Q(roll_no__icontains=q) | Q(email__icontains=q)
        )
    return render(request, 'students/student_list.html', {
        'students': students,
        'search_form': form,
    })


@faculty_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/student_detail.html', {'student': student})


@faculty_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        student = form.save(commit=False)
        if form.cleaned_data.get('create_login'):
            username = student.roll_no.lower()
            user = User.objects.create_user(
                username=username,
                email=student.email,
                password=form.cleaned_data['password'],
                first_name=student.name.split()[0],
            )
            student_group, _ = Group.objects.get_or_create(name=settings.STUDENT_GROUP)
            user.groups.add(student_group)
            student.user = user
        student.save()
        messages.success(request, f'Student {student.name} added successfully.')
        return redirect('students:list')
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add Student'})


@faculty_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    form.fields.pop('create_login', None)
    form.fields.pop('password', None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if student.user:
            student.user.email = student.email
            student.user.first_name = student.name.split()[0]
            student.user.save()
        messages.success(request, f'Student {student.name} updated successfully.')
        return redirect('students:list')
    return render(request, 'students/student_form.html', {
        'form': form,
        'title': 'Update Student',
        'student': student,
    })


@faculty_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.name
        if student.user:
            student.user.delete()
        else:
            student.delete()
        messages.success(request, f'Student {name} deleted successfully.')
        return redirect('students:list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


# ──────────────────────────────────────────────────────────────
# Advanced Analytics / Filter view
# ──────────────────────────────────────────────────────────────

@faculty_required
def student_analytics(request):
    """
    Advanced filter + analytics page.
    Filters: department, year, backlog status, min marks %, min attendance %.
    Outputs: summary cards, section table, top performers, backlog list,
             full filtered student table.
    """
    pass_threshold = settings.PASS_PERCENTAGE

    # ── read filters ────────────────────────────────────────────
    dept_filter    = request.GET.get('department', '')
    year_filter    = request.GET.get('year', '')
    backlog_filter = request.GET.get('backlog', '')       # 'yes' | 'no' | ''
    min_marks      = request.GET.get('min_marks', '')     # e.g. '60'
    max_marks_pct  = request.GET.get('max_marks', '')     # e.g. '80'
    min_att        = request.GET.get('min_att', '')       # e.g. '75'
    sort_by        = request.GET.get('sort', 'name')      # name | marks | att | backlogs

    filters_active = any([dept_filter, year_filter, backlog_filter, min_marks, max_marks_pct, min_att])

    # ── base queryset ────────────────────────────────────────────
    students_qs = Student.objects.all().order_by('roll_no')
    if dept_filter:
        students_qs = students_qs.filter(department=dept_filter)
    if year_filter:
        students_qs = students_qs.filter(year=year_filter)

    # ── compute per-student stats ────────────────────────────────
    all_stats = [_student_stats(s, pass_threshold) for s in students_qs]

    # ── apply marks / attendance / backlog filters ───────────────
    filtered = []
    for row in all_stats:
        pct = row['overall_pct']

        if min_marks and pct is not None and pct < float(min_marks):
            continue
        if max_marks_pct and pct is not None and pct > float(max_marks_pct):
            continue
        if min_att and row['att_pct'] < float(min_att):
            continue
        if backlog_filter == 'yes' and not row['has_backlog']:
            continue
        if backlog_filter == 'no' and row['has_backlog']:
            continue

        filtered.append(row)

    # ── sort ─────────────────────────────────────────────────────
    if sort_by == 'marks':
        filtered.sort(key=lambda r: r['overall_pct'] or 0, reverse=True)
    elif sort_by == 'att':
        filtered.sort(key=lambda r: r['att_pct'], reverse=True)
    elif sort_by == 'backlogs':
        filtered.sort(key=lambda r: r['backlog_count'], reverse=True)
    else:
        filtered.sort(key=lambda r: r['student'].name)

    # ── summary cards ────────────────────────────────────────────
    total_students  = len(filtered)
    with_backlogs   = sum(1 for r in filtered if r['has_backlog'])
    top_scorers     = [r for r in sorted(filtered, key=lambda r: r['overall_pct'] or 0, reverse=True) if r['overall_pct'] is not None][:5]
    avg_marks       = round(sum(r['overall_pct'] for r in filtered if r['overall_pct'] is not None) /
                            max(1, sum(1 for r in filtered if r['overall_pct'] is not None)), 1) if filtered else 0
    avg_att         = round(sum(r['att_pct'] for r in filtered) / max(1, total_students), 1)

    # ── section (dept × year) strength ───────────────────────────
    section_map = {}
    for row in filtered:
        s   = row['student']
        key = (s.department, s.year)
        if key not in section_map:
            section_map[key] = {
                'department': s.department,
                'year': s.year,
                'total': 0,
                'with_backlog': 0,
                'marks_sum': 0,
                'marks_count': 0,
                'att_sum': 0,
            }
        section_map[key]['total'] += 1
        if row['has_backlog']:
            section_map[key]['with_backlog'] += 1
        if row['overall_pct'] is not None:
            section_map[key]['marks_sum']  += row['overall_pct']
            section_map[key]['marks_count'] += 1
        section_map[key]['att_sum'] += row['att_pct']

    section_stats = []
    for key, data in sorted(section_map.items()):
        avg_m = round(data['marks_sum'] / data['marks_count'], 1) if data['marks_count'] else None
        avg_a = round(data['att_sum'] / data['total'], 1) if data['total'] else 0
        section_stats.append({
            **data,
            'avg_marks': avg_m,
            'avg_att': avg_a,
        })

    # ── dropdown options ─────────────────────────────────────────
    all_departments = (
        Student.objects.values_list('department', flat=True).distinct().order_by('department')
    )
    all_years = (
        Student.objects.values_list('year', flat=True).distinct().order_by('year')
    )

    return render(request, 'students/student_analytics.html', {
        'filtered':         filtered,
        'total_students':   total_students,
        'with_backlogs':    with_backlogs,
        'top_scorers':      top_scorers,
        'avg_marks':        avg_marks,
        'avg_att':          avg_att,
        'section_stats':    section_stats,
        'all_departments':  all_departments,
        'all_years':        all_years,
        # active filter values (to re-populate form)
        'f_dept':           dept_filter,
        'f_year':           year_filter,
        'f_backlog':        backlog_filter,
        'f_min_marks':      min_marks,
        'f_max_marks':      max_marks_pct,
        'f_min_att':        min_att,
        'f_sort':           sort_by,
        'filters_active':   filters_active,
        'pass_threshold':   pass_threshold,
    })
