from django.urls import path

from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('add/', views.exam_create, name='exam_add'),
    path('<int:pk>/', views.exam_detail, name='exam_detail'),
    path('<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    path('<int:pk>/report/<int:student_pk>/', views.report_card_view, name='report_card'),
    path('subjects/<int:pk>/delete/', views.exam_subject_delete, name='exam_subject_delete'),
    path('subjects/<int:pk>/marks/', views.marks_entry, name='marks_entry'),
    path('me/', views.my_results, name='results_me'),
]
