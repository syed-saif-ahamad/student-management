from django.urls import path

from . import views

app_name = 'fees'

urlpatterns = [
    # Faculty dashboard & list
    path('',                           views.fee_dashboard,        name='dashboard'),
    path('list/',                      views.fee_list,             name='list'),

    # Fee structures (faculty only)
    path('structure/',                 views.fee_structure_list,   name='structure_list'),
    path('structure/add/',             views.fee_structure_create, name='structure_create'),
    path('structure/<int:pk>/edit/',   views.fee_structure_edit,   name='structure_edit'),
    path('structure/<int:pk>/delete/', views.fee_structure_delete, name='structure_delete'),

    # Student fee records (faculty only)
    path('record/add/',                views.student_fee_create,   name='create'),
    path('record/<int:pk>/',           views.student_fee_detail,   name='detail'),
    path('record/<int:pk>/edit/',      views.student_fee_edit,     name='edit'),
    path('record/<int:pk>/delete/',    views.student_fee_delete,   name='delete'),
    path('record/<int:fee_pk>/pay/',   views.add_payment,          name='add_payment'),

    # Faculty: per-student summary
    path('student/<int:student_pk>/',  views.fee_student_summary,  name='student_summary'),

    # Student: my fees (read-only)
    path('my/',                        views.my_fees,              name='my_fees'),
]
