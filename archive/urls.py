from django.urls import path
from . import views

app_name = 'archive'

urlpatterns = [
    # لوحة التحكم
    path('', views.archive_dashboard, name='dashboard'),
    
    # الكتب الواردة والصادرة
    path('letters/', views.letter_list, name='letter_list'),
    path('letters/add/', views.letter_add, name='letter_add'),
    path('letters/<int:pk>/', views.letter_detail, name='letter_detail'),
    path('letters/<int:pk>/edit/', views.letter_edit, name='letter_edit'),
    path('letters/<int:pk>/delete/', views.letter_delete, name='letter_delete'),
    
    # وثائق المرشحين
    path('candidates/', views.candidate_document_list, name='candidate_document_list'),
    path('candidates/add/', views.candidate_document_add, name='candidate_document_add'),
    path('candidates/<int:pk>/', views.candidate_document_detail, name='candidate_document_detail'),
    path('candidates/<int:pk>/edit/', views.candidate_document_edit, name='candidate_document_edit'),
    path('candidates/<int:pk>/delete/', views.candidate_document_delete, name='candidate_document_delete'),
    
    # الفورمات الجاهزة
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.template_add, name='template_add'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/download/', views.template_download, name='template_download'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    
    # مجلدات الأرشيف
    path('folders/', views.archive_folder_list, name='folder_list'),
    
    # الوثائق المؤرشفة
    path('documents/', views.archived_document_list, name='archived_document_list'),
    path('documents/add/', views.archived_document_add, name='archived_document_add'),
    path('documents/<int:pk>/', views.archived_document_detail, name='archived_document_detail'),
    path('documents/<int:pk>/edit/', views.archived_document_edit, name='archived_document_edit'),
    path('documents/<int:pk>/download/', views.archived_document_download, name='archived_document_download'),
    path('documents/<int:pk>/delete/', views.archived_document_delete, name='archived_document_delete'),

    # استمارة معلومات المرشحين (إحسان منور)
    path('forms/candidate-info/', views.candidate_info_list, name='candidate_info_list'),
    path('forms/candidate-info/add/', views.candidate_info_add, name='candidate_info_add'),
    path('forms/candidate-info/<int:pk>/', views.candidate_info_detail, name='candidate_info_detail'),
    path('forms/candidate-info/<int:pk>/edit/', views.candidate_info_edit, name='candidate_info_edit'),

    # استمارة مقابلة المرشحين
    path('forms/candidate-interview/', views.candidate_interview_list, name='candidate_interview_list'),
    path('forms/candidate-interview/add/', views.candidate_interview_add, name='candidate_interview_add'),
    path('forms/candidate-interview/<int:pk>/', views.candidate_interview_detail, name='candidate_interview_detail'),
    path('forms/candidate-interview/<int:pk>/edit/', views.candidate_interview_edit, name='candidate_interview_edit'),
]
