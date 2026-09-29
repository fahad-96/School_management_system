from django.urls import path

from . import views

urlpatterns = [
    path('mark/', views.mark_attendance, name='attendance_mark'),
    path('report/', views.class_report, name='attendance_class_report'),
    path('student/<int:pk>/', views.student_report, name='attendance_student'),
    path('me/', views.my_attendance, name='attendance_me'),
]
