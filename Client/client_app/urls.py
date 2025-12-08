
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
]