# In Client/client_app/views.py
import grpc
import library_pb2
import library_pb2_grpc
from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from django.core.files.storage import FileSystemStorage 
from .grpc_client import LibraryClient 
from django.contrib import messages
from django.db.models import Q
###commendes####
from django.shortcuts import  get_object_or_404

from django.http import JsonResponse
from datetime import datetime, timedelta
from client_app.models import Client

from .models import Client, Loan, Book









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


# ----------------------------------------------------
# C. Staff Profile & User Management Views 
# ----------------------------------------------------

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
# --- UTILITAIRE : CONNEXION GRPC ---
def get_stub():
    channel = grpc.insecure_channel('localhost:50051')
    return library_pb2_grpc.LibraryServiceStub(channel)

# --- 1. LISTE DES CLIENTS (Design Photo 4 & 5) ---
def client_list(request):
    query = request.GET.get('q', '')  # récupère la valeur de recherche
    clients = []

    try:
        stub = get_stub()  # ton stub gRPC
        grpc_request = library_pb2.SearchRequest(query="")  # on récupère tous les clients
        client_stream = stub.GetAllClients(grpc_request)
        
        # Construire la liste Python
        for c in client_stream:
            clients.append({
                'id': c.id,
                'nom': c.nom,
                'email': c.email,
                'telephone': c.telephone,
                'adresse': c.adresse,
                'date_inscription': c.date_inscription
            })
        
        # 🔹 Filtrage côté Django si query n'est pas vide
        if query:
            query_lower = query.lower()
            clients = [
                c for c in clients
                if query_lower in c['nom'].lower() or query_lower in c['email'].lower()
            ]
    
    except Exception as e:
        messages.error(request, f"Erreur de connexion au serveur gRPC : {e}")

    return render(request, 'clients_list.html', {'clients': clients, 'query': query})

# --- 2. CRÉATION DE CLIENT (Design Photo 2 & 3) ---
def create_client(request):
    if request.method == 'POST':
        try:
            stub = get_stub()

            nouveau_client = library_pb2.Client(
                nom=request.POST.get('nom'),
                email=request.POST.get('email'),
                telephone=request.POST.get('telephone'),
                adresse=request.POST.get('adresse')
            )

            response = stub.CreateClient(nouveau_client)

            if response.success:
                # Cette ligne ne causera plus d'erreur NameError
                messages.success(request, "✅ Client enregistré avec succès")
                # Redirection vers la liste après le succès
                return redirect('clients_list') 
            else:
                messages.error(request, response.message)

        except Exception as e:
            # Cette ligne ne causera plus d'erreur NameError
            messages.error(request, f"Erreur gRPC : {e}")

    return render(request, 'clients_form.html', {
        'title': 'Nouveau Client'
    }
)
def edit_client(request, client_id):
    if not request.session.get('staff_id'):
        return redirect('staff_login')

    client_grpc = LibraryClient()
    
    # 1. On récupère les détails (Indispensable pour remplir le formulaire)
    client_details = client_grpc.get_client_details(client_id)
    
    # Si gRPC ne renvoie rien, on ne peut pas éditer
    if not client_details or not client_details.nom:
        print(f"Erreur : Client {client_id} introuvable via gRPC")
        return redirect('clients_list')

    context = {
        'client_id': client_id,
        'client_details': client_details # On passe l'objet au template
    }

    if request.method == 'POST':
        # ... (votre logique de mise à jour gRPC reste la même)
        response = client_grpc.update_client(
            client_id=client_id,
            nom=request.POST.get('nom'),
            email=request.POST.get('email'),
            telephone=request.POST.get('telephone'),
            adresse=request.POST.get('adresse')
        )
        if response.success:
            return redirect('clients_list')
        else:
            context['error_message'] = response.message

    # On utilise le fichier que vous venez de renommer
    return render(request, 'client_app/edit_client.html', context)# --- 4. SUPPRESSION DE CLIENT (Bouton rouge) ---
def delete_client_action(request, client_id):
    if request.method == 'POST':
        try:
            # 1. Connexion gRPC
            stub = get_stub() # ou votre méthode de connexion
            
            # 2. Appel de la suppression (Vérifiez le nom du champ dans votre .proto)
            # Souvent c'est client_id ou id
            request_grpc = library_pb2.ClientIdRequest(client_id=int(client_id))
            response = stub.DeleteClient(request_grpc)
            
            if response.success:
                messages.success(request, "Client supprimé avec succès !")
            else:
                messages.error(request, f"Erreur : {response.message}")
                
        except Exception as e:
            print(f"DEBUG: Erreur lors de la suppression : {e}")
            messages.error(request, "Erreur de connexion au serveur gRPC")

    # 3. On revient TOUJOURS à la liste
    return redirect('clients_list')



####commendes#####

def loan_list(request):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """Vue pour afficher la liste des emprunts"""
    # Récupérer les filtres
    status_filter = request.GET.get('status', 'ALL')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    loans = Loan.objects.select_related('client', 'book').all()
    
    # Appliquer les filtres
    if status_filter != 'ALL':
        loans = loans.filter(status=status_filter)
    
    if search_query:
        loans = loans.filter(
            Q(client__first_name__icontains=search_query) |
            Q(client__last_name__icontains=search_query) |
            Q(client__email__icontains=search_query) |
            Q(book__title__icontains=search_query) |
            Q(book__author__icontains=search_query)
        )
    
    # Statistiques
    stats = {
        'active_loans': Loan.objects.count(),
        #'overdue_loans': Loan.objects.filter(status='OVERDUE').count(),
        #'returns_today': Loan.objects.filter(
           # due_date=datetime.now().date(),
           # status='ACTIVE'
       # ).count()
    }
    
    context = {
        'loans': loans,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'loans/loan_list.html', context)



def loan_create(request):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """Vue pour créer un nouvel emprunt"""
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        book_id = request.POST.get('book_id')
        due_date = request.POST.get('due_date')
        
        try:
            client = Client.objects.get(id=client_id)
            book = Book.objects.get(id=book_id)
            
            # Vérifier la disponibilité
            if book.available_copies <= 0:
                messages.error(request, f"❌ Le livre '{book.title}' n'est pas disponible")
                return redirect('loans:loan_create')
            
            # Vérifier si le client peut emprunter
            if not client.can_borrow():
                messages.error(request, f"❌ {client.full_name} a atteint la limite d'emprunts (5 max)")
                return redirect('loans:loan_create')
            
            # Créer l'emprunt
            loan = Loan.objects.create(
                client=client,
                book=book,
                due_date=due_date,
                created_by=request.user
            )
            
            # Mettre à jour les copies disponibles
            book.available_copies -= 1
            book.save()
            
            messages.success(request, f"✅ Emprunt créé avec succès pour {client.full_name}")
            return redirect('loans:loan_list')
            
        except Client.DoesNotExist:
            messages.error(request, "❌ Client introuvable")
        except Book.DoesNotExist:
            messages.error(request, "❌ Livre introuvable")
        except Exception as e:
            messages.error(request, f"❌ Erreur: {str(e)}")
        
        return redirect('loan_create')
    
    # GET request
    #clients = Client.objects.filter(is_active=True).order_by('first_name')
    clients = Client.objects.all().order_by('nom') 
   # books = Book.objects.filter(available_copies__gt=0).order_by('title')
    books = Book.objects.all().order_by('title')
    # Date de retour par défaut (14 jours)
    default_due_date = (datetime.now() + timedelta(days=14)).date()
    
    context = {
        'clients': clients,
        'books': books,
        'default_due_date': default_due_date,
    }
    
    return render(request, 'loans/loan_create.html', context)



def loan_detail(request, loan_id):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """Vue pour afficher les détails d'un emprunt"""
    loan = get_object_or_404(Loan.objects.select_related('client', 'book'), id=loan_id)
    
    context = {
        'loan': loan,
    }
    
    return render(request, 'loans/loan_detail.html', context)



def loan_return(request, loan_id):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """Vue pour retourner un livre"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    if loan.status == 'RETURNED':
        messages.warning(request, "⚠️ Ce livre a déjà été retourné")
        return redirect('loans:loan_detail', loan_id=loan_id)
    
    if request.method == 'POST':
        loan.return_date = datetime.now()
        loan.status = 'RETURNED'
        loan.save()
        
        # Mettre à jour les copies disponibles
        loan.book.available_copies += 1
        loan.book.save()
        
        messages.success(request, f"✅ Livre '{loan.book.title}' retourné avec succès")
        return redirect('loans:loan_list')
    
    return render(request, 'loans/loan_return_confirm.html', {'loan': loan})


# ============================================================================
# API ENDPOINTS (AJAX)
# ============================================================================


def loan_stats_api(request):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """API pour récupérer les statistiques en temps réel"""
    stats = {
        'active_loans': Loan.objects.filter(status='ACTIVE').count(),
        'overdue_loans': Loan.objects.filter(status='OVERDUE').count(),
        'returns_today': Loan.objects.filter(
            due_date=datetime.now().date(),
            status='ACTIVE'
        ).count(),
        'total_clients': Client.objects.filter(is_active=True).count()
    }
    
    return JsonResponse(stats)



def search_clients_api(request):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """API pour rechercher des clients (autocomplete)"""
    query = request.GET.get('q', '')
    
    clients = Client.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query),
        is_active=True
    )[:10]  # Limiter à 10 résultats
    
    data = [
        {
            'id': c.id,
            'name': c.full_name,
            'email': c.email,
            'active_loans': c.active_loans_count
        }
        for c in clients
    ]
    
    return JsonResponse({'clients': data})



def available_books_api(request):
    if not request.session.get('staff_id'):
        request.session['login_message'] = "Veuillez vous connecter."
        return redirect('staff_login')
    """API pour récupérer les livres disponibles (autocomplete)"""
    query = request.GET.get('q', '')
    
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(author__icontains=query) |
        Q(isbn__icontains=query),
        available_copies__gt=0
    )[:10]  # Limiter à 10 résultats
    
    data = [
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'isbn': b.isbn,
            'available': b.available_copies
        }
        for b in books
    ]
    
    return JsonResponse({'books': data})