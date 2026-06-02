from django.contrib import admin

from .models import Marks, MarksAuditLog


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display  = ('student', 'subject', 'exam_type', 'marks', 'max_marks', 'exam_date', 'updated_by', 'updated_at')
    list_filter   = ('exam_type', 'subject')
    search_fields = ('student__name', 'student__roll_no', 'subject')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')


@admin.register(MarksAuditLog)
class MarksAuditLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'action', 'roll_no', 'student_name', 'subject', 'exam_type', 'marks_value', 'max_marks_value', 'performed_by')
    list_filter   = ('action', 'performed_by')
    search_fields = ('roll_no', 'student_name', 'subject', 'performed_by__username')
    readonly_fields = ('marks', 'action', 'performed_by', 'timestamp', 'student_name',
                       'roll_no', 'subject', 'exam_type', 'marks_value', 'max_marks_value',
                       'exam_date', 'changes')

    def has_add_permission(self, request):
        return False   # audit logs must not be created manually

    def has_change_permission(self, request, obj=None):
        return False   # audit logs are immutable
