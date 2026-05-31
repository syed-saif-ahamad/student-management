from django.contrib import messages
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import faculty_required, student_required
from students.models import Student

from .forms import MarksForm
from .models import Marks


@faculty_required
def marks_list(request):
    records = Marks.objects.select_related('student').all()
    subject = request.GET.get('subject')
    exam_type = request.GET.get('exam_type')
    student_id = request.GET.get('student')
    if subject:
        records = records.filter(subject__icontains=subject)
    if exam_type:
        records = records.filter(exam_type=exam_type)
    if student_id:
        records = records.filter(student_id=student_id)
    students = Student.objects.all()
    subjects = Marks.objects.values_list('subject', flat=True).distinct()
    return render(request, 'marks/marks_list.html', {
        'records': records,
        'students': students,
        'subjects': subjects,
        'exam_types': Marks.EXAM_TYPE_CHOICES,
        'filters': {'subject': subject, 'exam_type': exam_type, 'student': student_id},
    })


@faculty_required
def marks_create(request):
    form = MarksForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Marks added successfully.')
        return redirect('marks:list')
    return render(request, 'marks/marks_form.html', {'form': form, 'title': 'Add Marks'})


@faculty_required
def marks_update(request, pk):
    record = get_object_or_404(Marks, pk=pk)
    form = MarksForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Marks updated successfully.')
        return redirect('marks:list')
    return render(request, 'marks/marks_form.html', {
        'form': form,
        'title': 'Update Marks',
    })


@faculty_required
def marks_delete(request, pk):
    record = get_object_or_404(Marks, pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Marks record deleted.')
        return redirect('marks:list')
    return render(request, 'marks/marks_confirm_delete.html', {'record': record})


@student_required
def my_marks(request):
    student = get_object_or_404(Student, user=request.user)
    records = Marks.objects.filter(student=student)
    subject_wise = (
        records.values('subject')
        .annotate(total=Sum('marks'), max_total=Sum('max_marks'))
        .order_by('subject')
    )
    return render(request, 'marks/my_marks.html', {
        'records': records,
        'subject_wise': subject_wise,
        'student': student,
    })
