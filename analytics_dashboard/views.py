import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from accounts.decorators import faculty_required, is_faculty, is_student, student_required
from attendance.views import calculate_attendance_percentage
from marks.models import Marks
from students.models import Student

from .ml_model import predict_final_score
from .services import get_faculty_dashboard_context, get_student_performance_data


@faculty_required
def faculty_dashboard(request):
    context = get_faculty_dashboard_context()
    return render(request, 'analytics/faculty_dashboard.html', context)


@student_required
def student_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    records = Marks.objects.filter(student=student)
    total = sum(r.marks for r in records)
    max_total = sum(r.max_marks for r in records)
    current_pct = round((total / max_total) * 100, 2) if max_total else 0
    prediction = predict_final_score(student)
    performance = get_student_performance_data(student)

    return render(request, 'analytics/student_dashboard.html', {
        'student': student,
        'attendance_pct': calculate_attendance_percentage(student),
        'current_pct': current_pct,
        'records': records,
        'prediction': prediction,
        'performance_labels': json.dumps(performance['labels']),
        'performance_values': json.dumps(performance['values']),
    })


@student_required
def download_report(request):
    student = get_object_or_404(Student, user=request.user)
    records = Marks.objects.filter(student=student)
    total = sum(r.marks for r in records)
    max_total = sum(r.max_marks for r in records)
    current_pct = round((total / max_total) * 100, 2) if max_total else 0

    html = render_to_string('analytics/report.html', {
        'student': student,
        'records': records,
        'attendance_pct': calculate_attendance_percentage(student),
        'current_pct': current_pct,
        'prediction': predict_final_score(student),
    })

    response = HttpResponse(html, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="report_{student.roll_no}.html"'
    return response
