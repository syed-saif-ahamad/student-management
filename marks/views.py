from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import faculty_required, student_required
from students.models import Student

from .forms import MarksForm
from .models import Marks, MarksAuditLog


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _snapshot(marks_obj):
    """Return a dict of the current field values for diff / audit."""
    return {
        'student':   str(marks_obj.student),
        'subject':   marks_obj.subject,
        'exam_type': marks_obj.exam_type,
        'marks':     marks_obj.marks,
        'max_marks': marks_obj.max_marks,
        'exam_date': str(marks_obj.exam_date),
    }


def _build_diff(before, after):
    """Return a human-readable string of changed fields."""
    lines = []
    for key in ('subject', 'exam_type', 'marks', 'max_marks', 'exam_date'):
        if before.get(key) != after.get(key):
            lines.append(f'{key}: "{before.get(key)}" → "{after.get(key)}"')
    return '; '.join(lines) if lines else 'No field changes.'


def _log(action, marks_obj, user, changes=''):
    MarksAuditLog.objects.create(
        marks=marks_obj if action != MarksAuditLog.ACTION_DELETE else None,
        action=action,
        performed_by=user,
        timestamp=timezone.now(),
        student_name=marks_obj.student.name,
        roll_no=marks_obj.student.roll_no,
        subject=marks_obj.subject,
        exam_type=marks_obj.exam_type,
        marks_value=marks_obj.marks,
        max_marks_value=marks_obj.max_marks,
        exam_date=marks_obj.exam_date,
        changes=changes,
    )


# ─────────────────────────────────────────────────────────────
# Faculty-only views  (RBAC: only faculty can write)
# ─────────────────────────────────────────────────────────────

@faculty_required
def marks_list(request):
    records = Marks.objects.select_related('student', 'updated_by').all()
    subject    = request.GET.get('subject')
    exam_type  = request.GET.get('exam_type')
    student_id = request.GET.get('student')

    if subject:
        records = records.filter(subject__icontains=subject)
    if exam_type:
        records = records.filter(exam_type=exam_type)
    if student_id:
        records = records.filter(student_id=student_id)

    students = Student.objects.all()
    subjects  = Marks.objects.values_list('subject', flat=True).distinct()

    return render(request, 'marks/marks_list.html', {
        'records':    records,
        'students':   students,
        'subjects':   subjects,
        'exam_types': Marks.EXAM_TYPE_CHOICES,
        'filters':    {'subject': subject, 'exam_type': exam_type, 'student': student_id},
    })


@faculty_required
def marks_create(request):
    form = MarksForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.created_by = request.user
        record.updated_by = request.user
        record.save()
        _log(MarksAuditLog.ACTION_CREATE, record, request.user)
        messages.success(request, f'Marks added for {record.student.name} — {record.subject}.')
        return redirect('marks:list')
    return render(request, 'marks/marks_form.html', {'form': form, 'title': 'Add Marks'})


@faculty_required
def marks_update(request, pk):
    record = get_object_or_404(Marks, pk=pk)
    before = _snapshot(record)

    form = MarksForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        updated.updated_by = request.user
        updated.save()
        after = _snapshot(updated)
        _log(MarksAuditLog.ACTION_UPDATE, updated, request.user, _build_diff(before, after))
        messages.success(request, f'Marks updated for {updated.student.name} — {updated.subject}.')
        return redirect('marks:list')
    return render(request, 'marks/marks_form.html', {
        'form':   form,
        'title':  'Update Marks',
        'record': record,
    })


@faculty_required
def marks_delete(request, pk):
    record = get_object_or_404(Marks, pk=pk)
    if request.method == 'POST':
        _log(MarksAuditLog.ACTION_DELETE, record, request.user)
        name    = record.student.name
        subject = record.subject
        record.delete()
        messages.success(request, f'Marks deleted for {name} — {subject}.')
        return redirect('marks:list')
    return render(request, 'marks/marks_confirm_delete.html', {'record': record})


@faculty_required
def marks_audit_log(request):
    """Faculty-only view of the full audit trail."""
    logs = MarksAuditLog.objects.select_related('performed_by').all()

    # optional filters
    action_filter  = request.GET.get('action', '')
    faculty_filter = request.GET.get('faculty', '')
    subject_filter = request.GET.get('subject', '')

    if action_filter:
        logs = logs.filter(action=action_filter)
    if faculty_filter:
        logs = logs.filter(performed_by__username__icontains=faculty_filter)
    if subject_filter:
        logs = logs.filter(subject__icontains=subject_filter)

    return render(request, 'marks/marks_audit_log.html', {
        'logs':           logs[:200],          # cap at 200 rows for performance
        'action_choices': MarksAuditLog.ACTION_CHOICES,
        'f_action':       action_filter,
        'f_faculty':      faculty_filter,
        'f_subject':      subject_filter,
    })


# ─────────────────────────────────────────────────────────────
# Student read-only view  (RBAC: no write access)
# ─────────────────────────────────────────────────────────────

@student_required
def my_marks(request):
    """
    Students see their own marks only — completely read-only.
    Any attempt to POST is rejected with 403.
    """
    if request.method != 'GET':
        return HttpResponseForbidden('Students cannot modify marks.')

    student = get_object_or_404(Student, user=request.user)
    records = Marks.objects.filter(student=student).select_related('updated_by')

    subject_wise = (
        records.values('subject')
        .annotate(total=Sum('marks'), max_total=Sum('max_marks'))
        .order_by('subject')
    )

    # Per-subject latest update info for display
    subject_last_updated = {}
    for rec in records:
        subj = rec.subject
        if subj not in subject_last_updated or rec.updated_at > subject_last_updated[subj]['updated_at']:
            subject_last_updated[subj] = {
                'updated_at': rec.updated_at,
                'updated_by': rec.updated_by.get_full_name() if rec.updated_by else 'Faculty',
            }

    return render(request, 'marks/my_marks.html', {
        'records':              records,
        'subject_wise':         subject_wise,
        'student':              student,
        'subject_last_updated': subject_last_updated,
    })
