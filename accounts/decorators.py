from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def is_faculty(user):
    return user.is_authenticated and (user.is_superuser or user_in_group(user, settings.FACULTY_GROUP))


def is_student(user):
    return user.is_authenticated and user_in_group(user, settings.STUDENT_GROUP)


def faculty_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_faculty(request.user):
            raise PermissionDenied('Faculty access required.')
        return view_func(request, *args, **kwargs)

    return wrapper


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_student(request.user):
            raise PermissionDenied('Student access required.')
        return view_func(request, *args, **kwargs)

    return wrapper
