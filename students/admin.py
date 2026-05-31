from django.contrib import admin

from attendance.models import Attendance
from marks.models import Marks
from students.models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_no', 'name', 'email', 'department', 'year']
    search_fields = ['roll_no', 'name', 'email']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['student__name', 'student__roll_no']


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks', 'max_marks', 'exam_date']
    list_filter = ['exam_type', 'subject']
    search_fields = ['student__name', 'subject']
