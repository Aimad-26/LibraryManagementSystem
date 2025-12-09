# In Client/client_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from django.core.files.storage import FileSystemStorage 
from .grpc_client import LibraryClient 
# NOTE: LibraryClient est importé ici et non dans les fonctions individuelles

# ----------------------------------------------------
# A. Authentication Views 
# ----------------------------------------------------

def staff_login(request: HttpRequest):
    # If already logged in
    if request.session.get('staff_id'):
        return redirect('dashboard')

    message = request.session.pop('login_message', None)

    # 🔹 Add your media images here
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        client = LibraryClient()
        auth_response = client.staff_login(username, password)

        if auth_response.success:
            request.session['staff_id'] = auth_response.user_id
            request.session['username'] = username
            return redirect('dashboard')
        else:
            message = auth_response.message

    context = {
        'message': message,
        'bg_image': bg_image,
        'logo_image': logo_image,
    }
    return render(request, 'client_app/login.html', context)


def staff_logout(request: HttpRequest):
    request.session.clear()
    request.session['login_message'] = "You have been logged out."
    return redirect('staff_login')


# ----------------------------------------------------
# B. Core Management Views 
# ----------------------------------------------------

def dashboard(request: HttpRequest):
    # 🔹 Images used on both login & dashboard
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"
<<<<<<< HEAD

=======
    
>>>>>>> 6add19d3e81c20b6bd3a58d3b348213ac8d0655e
    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Please log in to view the dashboard."
        return redirect('staff_login')

    query = request.GET.get('q', '')
    client = LibraryClient()
    book_results = client.search_books(query)

    context = {
        'username': request.session.get('username'),
        'query': query,
        'book_results': book_results,
        'title': "Librarian Dashboard & Search",
        'bg_image': bg_image,          # 👈 added
        'logo_image': logo_image,      # 👈 added
    }
    return render(request, 'client_app/dashboard.html', context)

<<<<<<< HEAD
# 🚀 ADD_BOOK VIEW WITH BACKGROUND IMAGE SUPPORT
=======
# 🚀 ADD_BOOK VIEW
>>>>>>> 6add19d3e81c20b6bd3a58d3b348213ac8d0655e
def add_book(request: HttpRequest):
    staff_id = request.session.get('staff_id')

    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')

    # 🔥 Background image path (stored in MEDIA folder)
    bg_image = "/media/book_covers/add_book_background.jpg"   # <-- CHANGE extension if needed

    context = {
        'username': request.session.get('username'),
        'title': "Add New Book",
        'bg_image': bg_image,  # 👈 Send to HTML
    }

    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')

        # Validate Quantity
        try:
            total_copies = int(request.POST.get('total_copies', 1))
            if total_copies <= 0:
                raise ValueError
        except ValueError:
            context['error_message'] = "Total Copies must be a positive number."
            return render(request, 'client_app/add_book.html', context)

        # Handle uploaded book cover
        image_file = request.FILES.get('image')
        image_path_string = None

        if image_file:
            fs = FileSystemStorage()
            image_path_string = fs.save(f'book_covers/{image_file.name}', image_file)

        # gRPC Client Call
        client = LibraryClient()
<<<<<<< HEAD
=======
        
        # 3. Call gRPC RPC
>>>>>>> 6add19d3e81c20b6bd3a58d3b348213ac8d0655e
        response = client.create_book(
            title=title,
            author=author,
            isbn=isbn,
            total_copies=total_copies,
            image_path=image_path_string
        )

        # Response Handling
        context['success'] = response.success
        context['message'] = response.message

        if response.success:
            context['message'] += f" (New ID: {response.entity_id})"
<<<<<<< HEAD

=======
            
>>>>>>> 6add19d3e81c20b6bd3a58d3b348213ac8d0655e
    return render(request, 'client_app/add_book.html', context)


# ----------------------------------------------------
# C. Staff Profile & User Management Views 
# ----------------------------------------------------

# 🚀 1. CREATE USER VIEW
def create_user(request: HttpRequest):
    """
    Handles the creation of a new Staff/Librarian account.
    """
    context = {
        'username_session': request.session.get('username'), 
        'title': "Créer un nouvel utilisateur"
    }

    if request.method == 'POST':
        
        # 1. Récupération des données POST
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Conserver les données soumises pour pré-remplir le formulaire
        context['username'] = username
        context['email'] = email
        
        # 2. Validation côté client (Password Match)
        if password != password_confirm:
            context['success'] = False
            context['message'] = "Erreur de validation : Les mots de passe ne correspondent pas."
            return render(request, 'client_app/create_user.html', context)
        
        # 3. Validation minimum (champs requis)
        if not username or not password:
            context['success'] = False
            context['message'] = "Nom d'utilisateur et mot de passe sont requis."
            return render(request, 'client_app/create_user.html', context)

        # 4. Appel gRPC pour la Création d'utilisateur
        client = LibraryClient()
        response = client.create_user(username, email, password)
        
        # 5. Traitement de la réponse gRPC
        context['success'] = response.success
        context['message'] = response.message
        
        if response.success:
            context['username'] = ''
            context['email'] = ''
            
            request.session['login_message'] = response.message + " Veuillez vous connecter."
            return redirect('staff_login')
        else:
            pass
            
    return render(request, 'client_app/create_user.html', context)


# 🚀 2. USERS LIST VIEW
def users_list(request: HttpRequest):
    """Affiche la liste de tous les utilisateurs staff."""
    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Authentification nécessaire pour voir les utilisateurs."
        return redirect('staff_login')
        
    client = LibraryClient()
    user_results = client.get_all_users()
    
    list_message = request.session.pop('list_message', None)
    list_error = request.session.pop('list_error', None)

    context = {
        'username_session': request.session.get('username'),
        'title': "Liste des Utilisateurs Staff",
        'user_results': user_results,
        'message': list_message,
        'error_message': list_error
    }
    
    return render(request, 'client_app/users_list.html', context)


# 🚀 3. EDIT USER VIEW (SIMPLIFIÉ SANS DOUBLE VÉRIFICATION DE MOT DE PASSE)
def edit_user(request: HttpRequest, user_id):
    """Gère l'affichage du formulaire et la soumission de l'édition d'utilisateur."""
    if not request.session.get('staff_id'):
        return redirect('staff_login')
    
    client = LibraryClient()
    context = {
        'username_session': request.session.get('username'),
        'title': "Éditer l'utilisateur",
        'user_id': user_id,
        'error_message': None,
        'success_message': None
    }

    if request.method == 'POST':
        # 1. Récupération des données POST
        new_username = request.POST.get('username')
        new_email = request.POST.get('email')
        # La vérification de sécurité a été retirée du Frontend pour simplification
        new_password = request.POST.get('new_password', '')

        # 🚀 FIX: Un seul appel gRPC. On envoie current_password="" pour que le Backend (grpc_handler) l'ignore.
        
        update_response = client.update_staff_profile(
            staff_id=user_id, # Target the user being edited
            new_username=new_username,
            new_email=new_email,
            current_password="", # <-- Fix: Envoi de chaîne vide pour éviter l'échec UNAUTHENTICATED
            new_password=new_password
        )
        
        if update_response.success:
            request.session['list_message'] = "Profil mis à jour avec succès."
            return redirect('users_list')
        else:
            context['error_message'] = update_response.message
            context['user_details'] = client.get_user_details(user_id) 
            
    else:
        # Affichage initial du formulaire (méthode GET)
        user_details = client.get_user_details(user_id)
        if not user_details or not user_details.user_id:
            request.session['list_error'] = "Utilisateur introuvable."
            return redirect('users_list')
            
        context['user_details'] = user_details

    return render(request, 'client_app/edit_user.html', context)


# 🚀 4. DELETE USER ACTION VIEW
def delete_user_action(request: HttpRequest, user_id):
    """Gère la désactivation d'un utilisateur (suppression logique) via POST."""
    if not request.session.get('staff_id') or request.method != 'POST':
        return redirect('users_list') 

    client = LibraryClient()
    response = client.delete_user(user_id)

    if response.success:
        request.session['list_message'] = response.message
    else:
        request.session['list_error'] = response.message

    return redirect('users_list')


# 5. STAFF PROFILE VIEW (Original)
def staff_profile(request: HttpRequest):
    """
    Handles staff profile viewing and updates for the CURRENTLY LOGGED-IN USER.
    """
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')
    
    # Initialization context
    context = {
        'username': request.session.get('username'),
        'email': request.session.get('email', 'Update your email address'), 
        'staff_id': staff_id,
        'title': "Librarian Profile"
    }
    
    if request.method == 'POST':
        
        new_username = request.POST.get('new_username', context['username']) 
        new_email = request.POST.get('new_email', context['email'])
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        
        # 2. Basic Validation: Must supply current password
        if not current_password:
            context['error_message'] = "Security Check: You must enter your current password to save any changes."
            context['username'] = new_username 
            context['email'] = new_email
            return render(request, 'client_app/staff_profile.html', context)

        # 3. Call gRPC RPC
        client = LibraryClient()
        response = client.update_staff_profile(
            staff_id=staff_id,
            new_username=new_username,
            new_email=new_email,
            current_password=current_password,
            new_password=new_password
        )

        # 4. Process gRPC Response (StatusResponse)
        if response.success:
            context['success_message'] = response.message
            
            # Update session details for display
            request.session['username'] = new_username
            if new_email:
                request.session['email'] = new_email

            # Clear session if password was changed (forces re-login)
            if new_password:
                request.session.clear()
                request.session['login_message'] = "Password changed successfully. Please log in again."
                return redirect('staff_login')

        else:
            context['error_message'] = response.message
            context['username'] = new_username 
            context['email'] = new_email 


    # Re-render the page with success/error messages
    return render(request, 'client_app/staff_profile.html', context)