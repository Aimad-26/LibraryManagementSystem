import grpc
from concurrent import futures
import os
import django
import sys
from django.contrib.auth import authenticate 
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q 
from django.db.utils import OperationalError
from django.db import IntegrityError
from django.db import transaction

# ----------------------------------------------------
# 1. ROBUST DJANGO ENVIRONMENT SETUP 
# ----------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_server.settings') 

try:
    print("Attempting Django setup...") 
    django.setup() 
    print("Django setup successful.")
except Exception as e:
    print(f"FATAL: Django setup failed. Details: {e}") 
    sys.exit(1)

# ----------------------------------------------------
# 2. Generated Code Imports (MUST BE AFTER django.setup())
# ----------------------------------------------------
from django.contrib.auth.models import User
from library_admin.models import Book 

import library_pb2
import library_pb2_grpc


# ----------------------------------------------------
# 3. The gRPC Servicer Implementation
# ----------------------------------------------------

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    
    # A. Authentication (Staff/Librarian Login - RPC: Unary)
    def UserLogin(self, request, context):
        """Authenticates a staff member for the Client application."""
        user = authenticate(
            username=request.username,
            password=request.password
        )
        response = library_pb2.LoginResponse()

        if user is not None and user.is_active:
            if user.is_staff or user.is_superuser:
                response.success = True
                response.user_id = str(user.id) 
                response.message = f"Staff login successful: {user.username}"
            else:
                response.success = False
                response.message = "Access Denied: Account lacks staff privileges."
        else:
            response.success = False
            response.user_id = ""
            response.message = "Invalid username or account is inactive."
            
        return response

    # B. Inventory Management (Book Creation - RPC: Unary)
    def CreateBook(self, request, context):
        """Creates a new Book record, handling quantity and image path."""
        response = library_pb2.StatusResponse()
        
        try:
            total_qty = request.total_copies if request.total_copies > 0 else 1
            image_path = request.image_url if request.image_url else None
            
            new_book = Book.objects.create(
                title=request.title,
                author=request.author,
                isbn=request.isbn,
                total_copies=total_qty,
                available_copies=total_qty, 
                image=image_path
            )
            
            response.success = True
            response.message = f"Book '{request.title}' successfully created."
            response.entity_id = new_book.id
            
        except IntegrityError:
            response.success = False
            response.message = f"Failed to create book: ISBN '{request.isbn}' already exists."
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(response.message)
            
        except Exception as e:
            response.success = False
            response.message = f"An unexpected database error occurred: {e}"
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(response.message)
            
        return response
    
    # C. Inventory Lookup (Book Search - RPC: Server Stream)
    def SearchBooks(self, request, context):
        """Searches books and streams results back to the client."""
        query = request.query
        
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).order_by('title')
        
        for book in books:
            yield library_pb2.Book(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                total_copies=book.total_copies,
                available_copies=book.available_copies,
                image_url=str(book.image) if book.image else ""
            )

    # D. Staff Profile Update & Creation (Contournement)
    def UpdateStaffProfile(self, request, context):
        """
        Met à jour un profil existant (si staff_id est fourni) 
        OU crée un nouvel utilisateur (si staff_id est vide).
        """
        response = library_pb2.StatusResponse()

        # 🚀 MODE CRÉATION D'UTILISATEUR (CONTOURNEMENT) 🚀
        if not request.staff_id:
            try:
                if not request.new_username or not request.new_password:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details("Nom d'utilisateur et mot de passe sont obligatoires pour la création.")
                    return library_pb2.StatusResponse(success=False, message="Nom d'utilisateur et mot de passe sont obligatoires.")

                user = User.objects.create_user(
                    username=request.new_username,
                    email=request.new_email,
                    password=request.new_password,
                    is_staff=True,
                    is_active=True
                )
                
                response.success = True
                response.message = f"Utilisateur staff '{user.username}' créé avec succès."
                response.entity_id = user.id
                return response

            except IntegrityError:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details("Le nom d'utilisateur ou l'email est déjà utilisé.")
                return library_pb2.StatusResponse(success=False, message="Erreur: Nom d'utilisateur/Email déjà utilisé.")
            
            except Exception as e:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Erreur interne lors de la création: {e}")
                return library_pb2.StatusResponse(success=False, message=f"Échec de la création: {e}")

        # MODE MISE À JOUR DE PROFIL (LOGIQUE ORIGINALE)
        try:
            staff_id_int = int(request.staff_id) 
            user = User.objects.get(id=staff_id_int) 
            
            # 🚀 FIX SÉCURITÉ : Vérifier le mot de passe UNIQUEMENT s'il est fourni (non vide).
            # Permet l'édition simple (nom/email) par l'Admin sans le mot de passe de la cible.
            if request.current_password:
                 if not check_password(request.current_password, user.password):
                    context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                    context.set_details("Security Check Failed: Current password is incorrect.")
                    return library_pb2.StatusResponse(success=False, message="Invalid current password.")
            
            with transaction.atomic():
                
                if request.new_username and request.new_username != user.username:
                    if User.objects.filter(username=request.new_username).exclude(id=user.id).exists():
                        context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                        context.set_details("Username already taken.")
                        return library_pb2.StatusResponse(success=False, message="Username already taken.")
                    user.username = request.new_username
                    
                if request.new_email:
                    user.email = request.new_email

                if request.new_password:
                    user.password = make_password(request.new_password)
                
                user.save()

            response.success = True
            response.message = "Profile updated successfully."
            response.entity_id = user.id

        except User.DoesNotExist: 
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Staff member not found.")
            response.success = False
            response.message = "Staff member not found."
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An unexpected server error occurred: {e}")
            response.success = False
            response.message = "Failed to update profile due to a server error."

        return response
        
    # ----------------------------------------------------
    # E. User Management: List
    # ----------------------------------------------------
    def GetAllUsers(self, request, context):
        """Récupère et stream tous les utilisateurs staff/admin."""
        
        users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
        
        for user in users:
            yield library_pb2.UserDetail(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                is_staff=user.is_staff,
                is_active=user.is_active,
                date_joined=user.date_joined.isoformat(),
                is_superuser=user.is_superuser
            )
            
    # ----------------------------------------------------
    # F. User Management: Get Detail (for Editing)
    # ----------------------------------------------------
    def GetUserDetail(self, request, context):
        """Récupère les détails d'un seul utilisateur par ID."""
        try:
            user_id = int(request.user_id)
            user = User.objects.get(id=user_id)

            return library_pb2.UserDetail(
                user_id=str(user.id),
                username=user.username,
                email=user.email,
                is_staff=user.is_staff,
                is_active=user.is_active,
                date_joined=user.date_joined.isoformat(),
                is_superuser=user.is_superuser
            )
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Utilisateur non trouvé.")
            return library_pb2.UserDetail()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Erreur interne: {e}")
            return library_pb2.UserDetail()

    # ----------------------------------------------------
    # G. User Management: Delete (Physical Delete)
    # ----------------------------------------------------
    def DeleteUser(self, request, context):
        """Supprime DÉFINITIVEMENT un compte utilisateur de la base de données."""
        response = library_pb2.StatusResponse()
        try:
            # 1. Pré-vérification de l'existence
            user_id = int(request.user_id)
            user = User.objects.get(id=user_id)
            user_name = user.username # Stocker le nom avant la suppression

            # 2. SECURITÉ : Interdire la suppression du Superutilisateur
            if user.is_superuser:
                response.success = False
                response.message = "Impossible de supprimer un Superutilisateur."
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                return response

            # 3. SUPPRESSION DÉFINITIVE (Hard Delete)
            user.delete() 

            response.success = True
            response.message = f"Utilisateur '{user_name}' (ID {user_id}) supprimé définitivement."
            response.entity_id = user_id

        except User.DoesNotExist:
            response.success = False
            response.message = "Utilisateur non trouvé."
            context.set_code(grpc.StatusCode.NOT_FOUND)
            
        except IntegrityError:
            # Erreur si l'utilisateur est lié à des transactions (prêts, etc.)
            response.success = False
            response.message = "Échec de la suppression: L'utilisateur a des données liées (ex: prêts) dans la base de données."
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            
        except Exception as e:
            response.success = False
            response.message = f"Erreur interne lors de la suppression: {e}"
            context.set_code(grpc.StatusCode.INTERNAL)

        return response


# ----------------------------------------------------
# 4. Server Initialization (Serve function remains the same)
# ----------------------------------------------------

def serve():
    """Starts the gRPC server on the designated port 50051."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(
        LibraryServicer(), server)
    
    server.add_insecure_port('[::]:50051') 
    server.start()
    print("gRPC Library Server started on port 50051")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("\nServer shut down gracefully.")


if __name__ == '__main__':
    try:
        # Simple database check to ensure connection works before starting server
        Book.objects.exists()
        serve()
    except OperationalError as e:
        print("\n--- FATAL ERROR: DATABASE CONNECTION FAILED ---")
        print("Please ensure your MySQL server is running and accessible.")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")