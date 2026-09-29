from django.urls import path

from . import views

urlpatterns = [
    path('structure/', views.structure_list, name='fee_structure_list'),
    path('structure/add/', views.structure_create, name='fee_structure_add'),
    path('structure/<int:pk>/edit/', views.structure_edit, name='fee_structure_edit'),
    path('structure/<int:pk>/delete/', views.structure_delete, name='fee_structure_delete'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_create, name='payment_add'),
    path('receipt/<int:pk>/', views.receipt, name='receipt'),
    path('student/<int:pk>/', views.student_statement, name='fee_statement'),
    path('me/', views.my_fees, name='fees_me'),
    path('dues/', views.dues, name='dues_report'),
]
