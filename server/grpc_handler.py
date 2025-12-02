# In server/grpc_handler.py

import grpc
from concurrent import futures
import os
import django
from django.contrib.auth import authenticate 
from django.db.models import Q # Used for complex field lookups

# --- 1. Django Setup (MUST be run before importing models) ---
# Replace 'library_system_server.settings' with your actual Django project settings path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system_server.settings')
django.setup()

# Import your custom models
from library_admin.models import LibraryUser, Book 

# Import generated protobuf code (ensure you ran protoc successfully first)
import library_pb2
import library_pb2_grpc


class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    
    # ----------------------------------------------------
    # A. Authentication (Staff/Librarian Login)
    # ----------------------------------------------------
    def UserLogin(self, request, context):
        """Authenticates a staff member for the Client application."""
        user = authenticate(
            username=request.username,
            password=request.password
        )
        
        response = library_pb2.LoginResponse()

        if user is not None and user.is_active:
            # Check for staff privileges (Librarian)
            if user.is_staff or user.is_superuser:
                response.success = True
                response.user_id = str(user.id) # Use Django User ID for session tracking
                response.message = f"Staff login successful: {user.username}"
            else:
                response.success = False
                response.message = "Access Denied: Account lacks staff privileges."
        else:
            response.success = False
            response.user_id = ""
            response.message = "Invalid username or account is inactive."
            
        return response
    
    # ----------------------------------------------------
    # B. Inventory Management (Book Creation)
    # ----------------------------------------------------
    def CreateBook(self, request, context):
        """
        RPC: Creates a new Book record in the database using Django ORM.
        """
        response = library_pb2.StatusResponse()
        
        try:
            # Create a new Django Book instance from the incoming Protobuf data
            new_book = Book.objects.create(
                title=request.title,
                author=request.author,
                isbn=request.isbn,
                is_available=request.is_available
            )
            
            # Populate and return the StatusResponse
            response.success = True
            response.message = f"Book '{request.title}' successfully created."
            response.entity_id = new_book.id
            
        except Exception as e:
            response.success = False
            response.message = f"Failed to create book: {e}"
            response.entity_id = 0
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(response.message)
            
        return response
        
    # ----------------------------------------------------
    # C. Inventory Lookup (Book Search)
    # ----------------------------------------------------
    def SearchBooks(self, request, context):
        """
        RPC: Searches books and streams results back.
        """
        query = request.query
        
        # Filter logic: search for query in title OR author
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).order_by('title')
        
        # Yield each Django model object as a Protobuf message
        for book in books:
            yield library_pb2.Book(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                is_available=book.is_available
            )

# ----------------------------------------------------
# D. Server Setup
# ----------------------------------------------------
def serve():
    """Starts the gRPC server on the designated port."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(
        LibraryServicer(), server)
    
    # 🚨 PORT CONFIGURATION: Listening on port 50051
    server.add_insecure_port('[::]:50051') 
    server.start()
    print("gRPC Library Server started on port 50051.")
    
    try:
        # Keep the main thread alive for the server to run
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("\nServer shut down gracefully.")


if __name__ == '__main__':
    # Add a check here for Django DB connection before starting the server
    from django.db.utils import OperationalError
    try:
        # Simple test to ensure the database connection is alive
        Book.objects.exists()
        serve()
    except OperationalError as e:
        print("\n--- FATAL ERROR: DATABASE CONNECTION FAILED ---")
        print("Please ensure your MySQL server is running and accessible.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")