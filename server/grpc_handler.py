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