from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'accounts'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.role_redirect, name='redirect'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]
