from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_list, name='list'),
    path('by-date/', views.attendance_by_date, name='by_date'),
    path('bulk/', views.bulk_attendance, name='bulk'),
    path('add/', views.attendance_create, name='create'),
    path('<int:pk>/edit/', views.attendance_update, name='update'),
    path('<int:pk>/delete/', views.attendance_delete, name='delete'),
    path('my/', views.my_attendance, name='my_attendance'),
]
