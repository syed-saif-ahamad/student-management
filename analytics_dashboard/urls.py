from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('report/download/', views.download_report, name='download_report'),
]
