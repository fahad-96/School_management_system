from django.urls import path

from . import views

urlpatterns = [
    path('me/', views.my_timetable, name='timetable_me'),
    path('class/<int:pk>/', views.class_timetable, name='class_timetable'),
    path('teacher/<int:pk>/', views.teacher_timetable, name='teacher_timetable'),
    path('period/<int:pk>/delete/', views.period_delete, name='period_delete'),
    path('slots/', views.slot_list, name='slot_list'),
    path('slots/add/', views.slot_create, name='slot_add'),
    path('slots/<int:pk>/edit/', views.slot_edit, name='slot_edit'),
    path('slots/<int:pk>/delete/', views.slot_delete, name='slot_delete'),
]
