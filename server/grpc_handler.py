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
