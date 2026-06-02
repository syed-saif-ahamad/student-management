from django.urls import path

from . import views

app_name = 'marks'

urlpatterns = [
    path('', views.marks_list, name='list'),
    path('add/', views.marks_create, name='create'),
    path('<int:pk>/edit/', views.marks_update, name='update'),
    path('<int:pk>/delete/', views.marks_delete, name='delete'),
    path('my/', views.my_marks, name='my_marks'),
    path('audit-log/', views.marks_audit_log, name='audit_log'),
]
