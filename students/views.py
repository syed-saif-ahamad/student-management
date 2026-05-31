from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import faculty_required
from django.conf import settings

from .forms import StudentForm, StudentSearchForm
from .models import Student


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
