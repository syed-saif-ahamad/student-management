import json
from datetime import datetime

import pandas as pd
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from attendance.models import Attendance
from attendance.views import calculate_attendance_percentage
from marks.models import Marks
from students.models import Student


def calculate_average_marks():
    data = Marks.objects.values('marks', 'max_marks')
    if not data:
        return 0
    df = pd.DataFrame(list(data))
    df['pct'] = (df['marks'] / df['max_marks']) * 100
    return round(df['pct'].mean(), 2)


def get_total_students():
    return Student.objects.count()


def get_top_performers(limit=5):
    students = Student.objects.all()
    rankings = []
    for student in students:
        records = Marks.objects.filter(student=student)
        if not records.exists():
            continue
        total = records.aggregate(s=Sum('marks'))['s'] or 0
        max_total = records.aggregate(s=Sum('max_marks'))['s'] or 1
        pct = round((total / max_total) * 100, 2)
        rankings.append({
            'student': student,
            'percentage': pct,
            'total_marks': total,
            'max_marks': max_total,
        })
    rankings.sort(key=lambda x: x['percentage'], reverse=True)
    return rankings[:limit]


def get_top_performer():
    top = get_top_performers(limit=1)
    return top[0] if top else None


def get_pass_fail_counts():
    threshold = settings.PASS_PERCENTAGE
    students = Student.objects.all()
    passed = 0
    failed = 0
    for student in students:
        records = Marks.objects.filter(student=student)
        if not records.exists():
            continue
        total = records.aggregate(s=Sum('marks'))['s'] or 0
        max_total = records.aggregate(s=Sum('max_marks'))['s'] or 1
        pct = (total / max_total) * 100
        if pct >= threshold:
            passed += 1
        else:
            failed += 1
    return passed, failed


def get_pass_percentage():
    passed, failed = get_pass_fail_counts()
    total = passed + failed
    if total == 0:
        return 0
    return round((passed / total) * 100, 2)


def get_overall_attendance_percentage():
    students = Student.objects.all()
    if not students.exists():
        return 0
    percentages = [calculate_attendance_percentage(s) for s in students]
    return round(sum(percentages) / len(percentages), 2)


def get_student_vs_marks_chart_data():
    data = []
    for student in Student.objects.all():
        records = Marks.objects.filter(student=student)
        if not records.exists():
            continue
        total = records.aggregate(s=Sum('marks'))['s'] or 0
        max_total = records.aggregate(s=Sum('max_marks'))['s'] or 1
        pct = round((total / max_total) * 100, 2)
        data.append({'name': student.name, 'percentage': pct})
    data.sort(key=lambda x: x['percentage'], reverse=True)
    return data[:10]


def get_monthly_attendance_trend():
    records = (
        Attendance.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .order_by('month')
    )
    df = pd.DataFrame(list(records))
    if df.empty:
        return {'labels': [], 'values': []}

    monthly = []
    for month_val in Attendance.objects.dates('date', 'month'):
        month_records = Attendance.objects.filter(
            date__year=month_val.year,
            date__month=month_val.month,
        )
        total = month_records.count()
        if total == 0:
            continue
        present = month_records.filter(
            status__in=[Attendance.STATUS_PRESENT, Attendance.STATUS_LATE]
        ).count()
        pct = round((present / total) * 100, 2)
        monthly.append({
            'label': month_val.strftime('%b %Y'),
            'value': pct,
        })
    return {
        'labels': [m['label'] for m in monthly],
        'values': [m['value'] for m in monthly],
    }


def get_recent_exams(limit=5):
    return Marks.objects.select_related('student').order_by('-exam_date')[:limit]


def get_recent_attendance(limit=5):
    return Attendance.objects.select_related('student').order_by('-date')[:limit]


def get_student_performance_data(student):
    records = Marks.objects.filter(student=student).order_by('exam_date')
    labels = []
    values = []
    for r in records:
        labels.append(f'{r.subject} ({r.exam_type})')
        values.append(r.percentage)
    return {'labels': labels, 'values': values}


def get_faculty_dashboard_context():
    passed, failed = get_pass_fail_counts()
    return {
        'total_students': get_total_students(),
        'average_marks': calculate_average_marks(),
        'top_performer': get_top_performer(),
        'pass_percentage': get_pass_percentage(),
        'attendance_percentage': get_overall_attendance_percentage(),
        'top_students': get_top_performers(5),
        'recent_exams': get_recent_exams(),
        'recent_attendance': get_recent_attendance(),
        'chart_student_marks': json.dumps(get_student_vs_marks_chart_data()),
        'chart_pass_fail': json.dumps({'passed': passed, 'failed': failed}),
        'chart_attendance_trend': json.dumps(get_monthly_attendance_trend()),
    }
