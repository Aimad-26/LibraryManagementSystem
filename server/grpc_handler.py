import os
import sys
from concurrent import futures
from datetime import datetime
import grpc

# ============================
# CONFIGURATION DJANGO
# ============================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# Définir les settings Django AVANT tout import Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_server.settings')

import django
django.setup()

print("✅ Django initialisé avec library_server.settings !")

# ============================
# IMPORTS DJANGO
# ============================
from django.db import transaction, IntegrityError
from django.db.utils import OperationalError
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User

from library_admin.models import Book, Client as ClientModel, Loan

# ============================
# IMPORTS gRPC
# ============================
import library_pb2
import library_pb2_grpc

# ========================================================================
# LOAN SERVICER
# ========================================================================
class LoanServicer:
    """Gère les opérations gRPC pour les emprunts"""

    def CreateLoan(self, request, context):
        try:
            client = ClientModel.objects.get(id=request.client_id)
        except ClientModel.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Client avec l'ID {request.client_id} non trouvé")
            return library_pb2.LoanResponse()
        try:
            book = Book.objects.get(id=request.book_id)
        except Book.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Livre avec l'ID {request.book_id} non trouvé")
            return library_pb2.LoanResponse()
        if book.available_copies <= 0:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(f"Le livre '{book.title}' n'est pas disponible")
            return library_pb2.LoanResponse()
        if not client.can_borrow():
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("Le client a atteint la limite d'emprunts")
            return library_pb2.LoanResponse()
        due_date = datetime.strptime(request.due_date, '%Y-%m-%d').date()
        loan = Loan.objects.create(client=client, book=book, due_date=due_date)
        book.available_copies -= 1
        book.save()
        return self._loan_to_response(loan)

    # … Ici tu peux garder toutes les méthodes GetLoan, ListLoans, UpdateLoan, ReturnBook, etc. …
    # N'oublie pas de mettre _loan_to_response()

# ========================================================================
# LIBRARY SERVICER PRINCIPAL
# ========================================================================
class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    def __init__(self):
        self.loan_servicer = LoanServicer()

    # ===== AUTHENTICATION =====
    def UserLogin(self, request, context):
        user = authenticate(username=request.username, password=request.password)
        response = library_pb2.LoginResponse()
        if user and user.is_active:
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

    # ===== CLIENT MANAGEMENT =====
    def CreateClient(self, request, context):
        try:
            client = ClientModel.objects.create(
                nom=request.nom,
                email=request.email,
                telephone=request.telephone,
                adresse=request.adresse
            )
            return library_pb2.StatusResponse(success=True, message="Client créé avec succès", entity_id=client.id)
        except Exception as e:
            return library_pb2.StatusResponse(success=False, message=str(e))

    def GetAllClients(self, request, context):
        clients = ClientModel.objects.all()
        for c in clients:
            yield library_pb2.Client(
                id=c.id,
                nom=c.nom,
                email=c.email,
                telephone=c.telephone,
                adresse=c.adresse,
                date_inscription=c.date_inscription.strftime("%d/%m/%Y")
            )

    # ===== DÉLÉGATION LOAN =====
    def CreateLoan(self, request, context):
        return self.loan_servicer.CreateLoan(request, context)
    
    # … idem pour GetLoan, ListLoans, UpdateLoan, ReturnBook, etc. …

# ========================================================================
# SERVER INITIALIZATION
# ========================================================================
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(LibraryServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("🚀 gRPC Library Server started on port 50051")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("✅ Server shut down gracefully.")

if __name__ == '__main__':
    try:
        Book.objects.exists()  # Test DB
        serve()
    except OperationalError:
        print("\n❌ FATAL ERROR: DATABASE CONNECTION FAILED. Vérifie MySQL.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
