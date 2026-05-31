from .decorators import is_faculty, is_student


def user_roles(request):
    if not request.user.is_authenticated:
        return {'is_faculty_user': False, 'is_student_user': False}
    return {
        'is_faculty_user': is_faculty(request.user),
        'is_student_user': is_student(request.user),
    }
