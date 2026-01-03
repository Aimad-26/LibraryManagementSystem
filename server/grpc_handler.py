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
# 2. Generated Code Imports
# ----------------------------------------------------
from django.contrib.auth.models import User
from library_admin.models import Book, Loan, Member 

import library_pb2
import library_pb2_grpc

# ----------------------------------------------------
# 3. The gRPC Servicer Implementation
# ----------------------------------------------------

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    
    # --- A. Authentication ---
    def UserLogin(self, request, context):
        user = authenticate(username=request.username, password=request.password)
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
            response.message = "Invalid username or account is inactive."
        return response

    # --- B. Inventory Management ---
    def CreateBook(self, request, context):
        try:
            total_qty = request.total_copies if request.total_copies > 0 else 1
            new_book = Book.objects.create(
                title=request.title,
                author=request.author,
                isbn=request.isbn,
                total_copies=total_qty,
                available_copies=total_qty, 
                image=request.image_url if request.image_url else None
            )
            return library_pb2.StatusResponse(success=True, message=f"Book created.", entity_id=new_book.id)
        except IntegrityError:
            return library_pb2.StatusResponse(success=False, message="ISBN already exists.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def UpdateBookAvailability(self, request, context):
        try:
            book = Book.objects.get(id=request.id)
            book.title = request.title
            book.author = request.author
            book.isbn = request.isbn
            book.total_copies = request.total_copies
            book.available_copies = request.available_copies
            book.save()
            return library_pb2.StatusResponse(success=True, message="Livre mis à jour.")
        except Book.DoesNotExist:
            return library_pb2.StatusResponse(success=False, message="Livre introuvable.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def DeleteBook(self, request, context):
        try:
            book_id = int(request.query)
            book = Book.objects.get(id=book_id)
            book.delete()
            return library_pb2.StatusResponse(success=True, message="Livre supprimé avec succès.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def GetBook(self, request, context):
        try:
            book = Book.objects.get(id=int(request.query))
            return library_pb2.Book(
                id=book.id, title=book.title, author=book.author,
                isbn=book.isbn, total_copies=book.total_copies,
                available_copies=book.available_copies,
                image_url=str(book.image) if book.image else ""
            )
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.Book()

    # --- C. Search ---
    def SearchBooks(self, request, context):
        query = request.query
        books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query)).order_by('title')
        for book in books:
            yield library_pb2.Book(
                id=book.id, title=book.title, author=book.author, isbn=book.isbn,
                total_copies=book.total_copies, available_copies=book.available_copies,
                image_url=str(book.image) if book.image else ""
            )

    # --- D. Members ---
    def CreateMember(self, request, context):
        try:
            member = Member.objects.create(full_name=request.full_name, email=request.email, phone=request.phone)
            return library_pb2.StatusResponse(success=True, message="Membre créé.", entity_id=member.id)
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def GetAllMembers(self, request, context):
        members = Member.objects.all().order_by('-id')
        for m in members:
            yield library_pb2.Member(
                id=str(m.id), full_name=m.full_name, email=m.email, phone=m.phone,
                date_joined=m.date_joined.isoformat() if m.date_joined else ""
            )

    def GetMemberDetail(self, request, context):
        try:
            m = Member.objects.get(id=int(request.user_id))
            return library_pb2.Member(id=str(m.id), full_name=m.full_name, email=m.email, phone=m.phone)
        except Exception:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.Member()

    def UpdateMember(self, request, context):
        try:
            member = Member.objects.get(id=int(request.id))
            member.full_name = request.full_name
            member.email = request.email
            member.phone = request.phone
            member.save()
            return library_pb2.StatusResponse(success=True, message="Membre mis à jour.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def DeleteMember(self, request, context):
        try:
            member = Member.objects.get(id=int(request.user_id))
            member.delete() 
            return library_pb2.StatusResponse(success=True, message="Membre supprimé.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    # --- E. Borrow & Return ---
    def BorrowBook(self, request, context):
        try:
            from django.utils import timezone
            from datetime import timedelta
            with transaction.atomic():
                book = Book.objects.select_for_update().get(id=int(request.book_id))
                if book.available_copies <= 0:
                    return library_pb2.StatusResponse(success=False, message="Stock épuisé.")
                member = Member.objects.get(id=int(request.member_id))
                Loan.objects.create(book=book, member=member, due_date=timezone.now().date() + timedelta(days=14))
                book.available_copies -= 1
                book.save()
                return library_pb2.StatusResponse(success=True, message="Emprunt réussi.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def ReturnBook(self, request, context):
        try:
            from django.utils import timezone
            with transaction.atomic():
                loan = Loan.objects.filter(book_id=request.book_id, member_id=int(request.member_id), returned_date__isnull=True).first()
                if not loan:
                    return library_pb2.StatusResponse(success=False, message="Aucun prêt actif.")
                loan.returned_date = timezone.now().date()
                loan.save()
                book = loan.book
                book.available_copies += 1
                book.save()
                return library_pb2.StatusResponse(success=True, message="Livre retourné.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    # --- F. Staff Management ---
    def GetAllUsers(self, request, context):
        users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
        for user in users:
            yield library_pb2.UserDetail(
                user_id=str(user.id), username=user.username, email=user.email,
                is_staff=user.is_staff, is_active=user.is_active,
                date_joined=user.date_joined.isoformat(), is_superuser=user.is_superuser
            )

    def GetUserDetail(self, request, context):
        try:
            user = User.objects.get(id=int(request.user_id))
            return library_pb2.UserDetail(
                user_id=str(user.id), username=user.username, email=user.email,
                is_staff=user.is_staff, is_active=user.is_active,
                date_joined=user.date_joined.isoformat(), is_superuser=user.is_superuser
            )
        except Exception:
            return library_pb2.UserDetail()

    def DeleteUser(self, request, context):
        try:
            user = User.objects.get(id=int(request.user_id))
            if user.is_superuser:
                return library_pb2.StatusResponse(success=False, message="Cannot delete superuser.")
            user.delete()
            return library_pb2.StatusResponse(success=True, message="User deleted.")
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def UpdateStaffProfile(self, request, context):
        response = library_pb2.StatusResponse()
        # MODE CRÉATION
        if not request.staff_id:
            try:
                user = User.objects.create_user(
                    username=request.new_username, email=request.new_email,
                    password=request.new_password, is_staff=True, is_active=True
                )
                response.success = True
                response.message = f"Utilisateur '{user.username}' créé."
                response.entity_id = user.id
                return response
            except Exception as e:
                return library_pb2.StatusResponse(success=False, message=str(e))

        # MODE MISE À JOUR
        try:
            user = User.objects.get(id=int(request.staff_id))
            if request.current_password and not check_password(request.current_password, user.password):
                return library_pb2.StatusResponse(success=False, message="Invalid current password.")
            
            with transaction.atomic():
                if request.new_username: user.username = request.new_username
                if request.new_email: user.email = request.new_email
                if request.new_password: user.password = make_password(request.new_password)
                user.save()
            response.success = True
            response.message = "Profile updated."
            response.entity_id = user.id
        except Exception as e:
            response.success = False
            response.message = str(e)
        return response

# ----------------------------------------------------
# 4. Server Initialization
# ----------------------------------------------------

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer_instance = LibraryServicer()
    library_pb2_grpc.add_LibraryServiceServicer_to_server(servicer_instance, server)
    server.add_insecure_port('[::]:50051') 
    server.start()
    print("✅ SERVEUR gRPC DÉMARRÉ SUR LE PORT 50051")
    server.wait_for_termination()
if __name__ == '__main__':
    try:
        serve()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
        sys.exit(0)