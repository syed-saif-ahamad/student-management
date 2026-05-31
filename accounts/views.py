from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .decorators import is_faculty, is_student
from .forms import CustomPasswordChangeForm, LoginForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:redirect')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('accounts:redirect')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def role_redirect(request):
    if is_faculty(request.user):
        return redirect('analytics:faculty_dashboard')
    if is_student(request.user):
        return redirect('analytics:student_dashboard')
    messages.warning(request, 'No role assigned. Contact administrator.')
    return redirect('accounts:login')


class ChangePasswordView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:change_password')

    def form_valid(self, form):
        messages.success(self.request, 'Password updated successfully.')
        return super().form_valid(form)
