# In Client/client_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from django.contrib import messages
from django.core.files.storage import FileSystemStorage 
from .grpc_client import LibraryClient 
from django.utils import timezone
from datetime import timedelta
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

# in client_app/views.py

def dashboard(request: HttpRequest):
    # 🔹 Images used on both login & dashboard
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"

    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Please log in to view the dashboard."
        return redirect('staff_login')

    query = request.GET.get('q', '')
    client = LibraryClient()
    
    # On convertit le stream gRPC en liste pour faire les calculs
    book_results = list(client.search_books(query))

    # --- NOUVELLE LOGIQUE DE STATISTIQUES ---
    total_available = 0
    total_borrowed = 0
    
    for book in book_results:
        total_available += book.available_copies
        # Le nombre d'empruntés est la différence entre le stock total et le stock disponible
        total_borrowed += (book.total_copies - book.available_copies)
    # ----------------------------------------

    context = {
        'username': request.session.get('username'),
        'query': query,
        'book_results': book_results,
        'total_available': total_available, # 👈 ajouté
        'total_borrowed': total_borrowed,   # 👈 ajouté
        'title': "Librarian Dashboard & Search",
        'bg_image': bg_image,
        'logo_image': logo_image,
    }
    return render(request, 'client_app/dashboard.html', context)

def return_book_view(request):
    client = LibraryClient()
    # On récupère l'ID du livre si on vient du bouton "Return" du Dashboard
    book_id = request.GET.get('book_id')
    
    if request.method == "POST":
        member_id = request.POST.get('member_id')
        book_id = request.POST.get('book_id')
        
        # Appel gRPC pour traiter le retour
        response = client.return_book(member_id, book_id)
        if response.success:
            messages.success(request, response.message)
            return redirect('dashboard')
        else:
            messages.error(request, response.message)

    members = list(client.get_all_members())
    books = list(client.search_books(query=""))
    
    return render(request, 'client_app/issue_book.html', {
        'members': members,
        'books': books,
        'preselected_book_id': book_id,
        'title': "Return a Book" # Optionnel : pour changer le titre
    })
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

    return render(request, 'client_app/add_book.html', context)

# --- Section Membres dans client_app/views.py ---
def issue_book_view(request):
    client = LibraryClient()
    book_id = request.GET.get('book_id')
    
    # 1. Récupérer les données pour les listes
    members = list(client.get_all_members())
    books = list(client.search_books(query=""))
    
    # 2. Déterminer le mode (Borrow ou Return) basé sur le stock
    target_book = next((b for b in books if str(b.id) == str(book_id)), None)
    is_return_mode = target_book.available_copies == 0 if target_book else False
    
    if request.method == "POST":
        action = request.POST.get('action')
        m_id = request.POST.get('member_id')
        b_id = request.POST.get('book_id')

        if action == "borrow":
            # Optionnel: on peut passer une due_date personnalisée ici
            response = client.borrow_book(m_id, b_id)
        elif action == "return":
            response = client.return_book(m_id, b_id)
        
        if response.success:
            messages.success(request, response.message)
            return redirect('dashboard')
        messages.error(request, response.message)

    return render(request, 'client_app/issue_book.html', {
        'members': members,
        'books': books,
        'preselected_book_id': book_id,
        'is_return_mode': is_return_mode,
        'default_due_date': (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    })
def members_list(request):
    """Affiche la liste complète des membres (clients)."""
    if not request.session.get('staff_id'):
        return redirect('staff_login')
        
    client = LibraryClient()
    # On récupère les membres via gRPC
    members = client.get_all_members() 
    
    context = {
        'members': members,
        'title': "Gestion des Membres",
        'username_session': request.session.get('username'),
    }
    return render(request, 'client_app/members.html', context)

def add_member(request):
    """Ajoute un nouveau client."""
    if not request.session.get('staff_id'):
        return redirect('staff_login')

    if request.method == 'POST':
        client = LibraryClient()
        client.create_member(
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone')
        )
        return redirect('members_list')
    
    return render(request, 'client_app/add_member.html', {'title': "Inscrire un Membre"})

def edit_member(request, member_id):
    """Affiche le formulaire et sauvegarde les modifications."""
    if not request.session.get('staff_id'):
        return redirect('staff_login')
        
    client = LibraryClient()
    
    if request.method == 'POST':
        client.update_member(
            m_id=str(member_id), # gRPC attend souvent des strings pour les IDs
            name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone')
        )
        return redirect('members_list')
    
    # Si GET : on récupère les détails pour remplir le formulaire
    member = client.get_member_detail(str(member_id))
    return render(request, 'client_app/edit_member.html', {'member': member, 'title': "Modifier Membre"})

def delete_member_action(request, member_id):
    """Suppression physique via gRPC."""
    if not request.session.get('staff_id'):
        return redirect('staff_login')
        
    if request.method == 'POST':
        client = LibraryClient()
        client.delete_member(str(member_id))
    return redirect('members_list')
# ----------------------------------------------------
# C. Staff Profile & User Management Views 
# ----------------------------------------------------

    member = client.get_member_detail(member_id)
    return render(request, 'client_app/edit_member.html', {'member': member})
# 🚀 1. CREATE USER VIEW
def create_user(request: HttpRequest):
    """
    Handles the creation of a new Staff/Librarian account.
    """
    # ✅ same media images used in login
    bg_image = "book_covers/Background.jpg"
    logo_image = "book_covers/ismac_logo.png"

    context = {
        'username_session': request.session.get('username'),
        'title': "Créer un nouvel utilisateur",
        'bg_image': bg_image,
        'logo_image': logo_image,
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