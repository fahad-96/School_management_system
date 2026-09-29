from django.urls import path

from . import views

urlpatterns = [
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/add/', views.StudentCreateView.as_view(), name='student_add'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('students/<int:pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),

    path('teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('teachers/add/', views.TeacherCreateView.as_view(), name='teacher_add'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='teacher_edit'),
    path('teachers/<int:pk>/delete/', views.TeacherDeleteView.as_view(), name='teacher_delete'),

    path('parents/', views.ParentListView.as_view(), name='parent_list'),
    path('parents/add/', views.ParentCreateView.as_view(), name='parent_add'),
    path('parents/<int:pk>/edit/', views.ParentUpdateView.as_view(), name='parent_edit'),
    path('parents/<int:pk>/delete/', views.ParentDeleteView.as_view(), name='parent_delete'),

    path('classes/', views.SchoolClassListView.as_view(), name='class_list'),
    path('classes/add/', views.SchoolClassCreateView.as_view(), name='class_add'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/<int:pk>/edit/', views.SchoolClassUpdateView.as_view(), name='class_edit'),
    path('classes/<int:pk>/delete/', views.SchoolClassDeleteView.as_view(), name='class_delete'),
    path('class-subjects/<int:pk>/delete/', views.class_subject_delete, name='class_subject_delete'),

    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/add/', views.SubjectCreateView.as_view(), name='subject_add'),
    path('subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    path('years/', views.AcademicYearListView.as_view(), name='year_list'),
    path('years/add/', views.AcademicYearCreateView.as_view(), name='year_add'),
    path('years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='year_edit'),
    path('years/<int:pk>/delete/', views.AcademicYearDeleteView.as_view(), name='year_delete'),
]
