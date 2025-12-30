
from django.urls import path
from . import views

urlpatterns = [
    # Login path handles both GET (display form) and POST (process form)
    path('login/', views.staff_login, name='staff_login'), 
    
    # Dashboard path handles the book search form submission (via GET parameters)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-book/', views.add_book, name='add_book'),
    path('profile/', views.staff_profile, name='staff_profile'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('', views.staff_login, name='home'), # Default route redirects to login
    path('users/create/', views.create_user, name='create_user'),
    path('users/', views.users_list, name='users_list'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user_action, name='delete_user_action'),
    # Gestion des Clients (CRUD complet gRPC)
    path('clients/', views.client_list, name='clients_list'),
    path('clients/add/', views.create_client, name='create_client'),
    path('clients/edit/<int:client_id>/', views.edit_client, name='edit_client'),
    path('clients/delete/<int:client_id>/', views.delete_client_action, name='delete_client_action'),
    ###commendes#####
    # ----------------- Loans / Emprunts -----------------
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/create/', views.loan_create, name='loan_create'),
    path('loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:loan_id>/return/', views.loan_return, name='loan_return'),

    # ----------------- APIs AJAX -----------------
    path('loans/api/stats/', views.loan_stats_api, name='loan_stats_api'),
    path('loans/api/clients/search/', views.search_clients_api, name='search_clients_api'),
    path('loans/api/books/available/', views.available_books_api, name='available_books_api'),
]