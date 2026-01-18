from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Chatbot API
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    
    # Investors
    path('investors/', views.investor_list, name='investor_list'),
    path('investors/add/', views.investor_create, name='investor_create'),
    path('investors/<int:pk>/', views.investor_detail, name='investor_detail'),
    path('investors/<int:pk>/edit/', views.investor_edit, name='investor_edit'),
    path('investors/<int:pk>/delete/', views.investor_delete, name='investor_delete'),
    
    # Artifacts
    path('artifacts/', views.artifact_list, name='artifact_list'),
    path('artifacts/add/', views.artifact_create, name='artifact_create'),
    path('artifacts/<int:pk>/edit/', views.artifact_edit, name='artifact_edit'),
    path('artifacts/<int:pk>/delete/', views.artifact_delete, name='artifact_delete'),
    
    # Email Drafts
    path('drafts/', views.draft_list, name='draft_list'),
    path('drafts/add/', views.draft_create, name='draft_create'),
    path('drafts/<int:pk>/edit/', views.draft_edit, name='draft_edit'),
    path('drafts/<int:pk>/delete/', views.draft_delete, name='draft_delete'),
    
    # Responses/Funding
    path('responses/', views.response_list, name='response_list'),
    path('responses/add/', views.response_create, name='response_create'),
    path('responses/<int:pk>/edit/', views.response_edit, name='response_edit'),
    path('responses/<int:pk>/delete/', views.response_delete, name='response_delete'),
    
    # Communication Logs
    path('communications/', views.communication_list, name='communication_list'),
]
