# In Client/client_app/grpc_client.py

import grpc
import sys
import os
####commendes###
from datetime import datetime


# ----------------------------------------------------
# 1. PYTHON PATH FIX (CRITICAL for Django Client)
# ----------------------------------------------------

current_app_dir = os.path.dirname(os.path.abspath(__file__))
project_root_client = os.path.abspath(os.path.join(current_app_dir, '..'))
sys.path.insert(0, project_root_client)

# ----------------------------------------------------
# 2. GENERATED CODE IMPORTS
# ----------------------------------------------------

import library_pb2
import library_pb2_grpc

SERVER_ADDRESS = 'localhost:50051' 

class LibraryClient:
    """
    Client-side wrapper to manage remote calls (RPCs) to the gRPC Server.
    """
    def __init__(self):
        self.channel = grpc.insecure_channel(SERVER_ADDRESS) 
        self.stub = library_pb2_grpc.LibraryServiceStub(self.channel)

    # ----------------------------------------------------
    # A. Authentication (Librarian Login)
    # ----------------------------------------------------
    def staff_login(self, username, password):
        """Calls the remote UserLogin RPC for staff authentication."""
        request = library_pb2.LoginRequest(username=username, password=password)
        try:
            response = self.stub.UserLogin(request)
            return response
        except grpc.RpcError as e:
            print(f"Error calling UserLogin RPC: {e.details()}")
            return library_pb2.LoginResponse(
                success=False, 
                message=f"Connection error to gRPC server: {e.details()}"
            )

    # ----------------------------------------------------
    # B. Inventory Lookup (Search)
    # ----------------------------------------------------
    
    def search_books(self, query):
        """Calls the remote SearchBooks RPC to retrieve a stream of books."""
        request = library_pb2.SearchRequest(query=query)
        
        try:
            return list(self.stub.SearchBooks(request))
        except grpc.RpcError as e:
            print(f"Error calling SearchBooks RPC: {e.details()}")
            return []

    # ----------------------------------------------------
    # C. Inventory Management (Create Book)
    # ----------------------------------------------------
    def create_book(self, title, author, isbn, total_copies, image_path=None):
        """Calls the remote CreateBook RPC on the server to add a new book."""
        
        book_request = library_pb2.Book(
            title=title,
            author=author,
            isbn=isbn,
            total_copies=total_copies, 
            image_url=image_path if image_path else "" 
        )
        
        try:
            response = self.stub.CreateBook(book_request)
            return response
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            print(f"Error calling CreateBook RPC. Status: {status_code.name}, Details: {details}")
            
            return library_pb2.StatusResponse(
                success=False, 
                message=f"RPC Failed ({status_code.name}): {details}"
            )

    # ----------------------------------------------------
    # D. Staff Profile (Update & Creation)
    # ----------------------------------------------------
    
    # D1. Base RPC Wrapper for Update (Used by create_user)
    def update_staff_profile(self, staff_id, new_username, new_email, current_password, new_password=""):
        """
        Calls the remote UpdateStaffProfile RPC to change staff credentials 
        or trigger user creation (if staff_id is empty).
        """
        request = library_pb2.UpdateProfileRequest(
            staff_id=str(staff_id), 
            new_username=new_username,
            new_email=new_email,
            current_password=current_password,
            new_password=new_password 
        )

        try:
            response = self.stub.UpdateStaffProfile(request)
            return response
            
        except grpc.RpcError as e:
            status_code = e.code()
            details = e.details()
            
            print(f"Error calling UpdateStaffProfile RPC. Status: {status_code.name}, Details: {details}")
            
            return library_pb2.StatusResponse(
                success=False, 
                message=f"RPC Failed ({status_code.name}): {details}"
            )
            
    # D2. Creation Wrapper (Uses update_staff_profile for detournement)
    def create_user(self, username, email, password):
        """Crée un nouvel utilisateur staff en détournant le RPC UpdateStaffProfile."""
        
        return self.update_staff_profile(
            staff_id="", 
            new_username=username,
            new_email=email,
            current_password="", 
            new_password=password 
        )

    # ----------------------------------------------------
    # E. User Management (List, Get, Delete) 🚀 NOUVEAU 🚀
    # ----------------------------------------------------
    
    def get_all_users(self):
        """Appelle le RPC GetAllUsers pour récupérer tous les utilisateurs."""
        request = library_pb2.SearchRequest(query="")
        try:
            return list(self.stub.GetAllUsers(request))
        except grpc.RpcError as e:
            print(f"Error calling GetAllUsers RPC: {e.details()}")
            return []

    def get_user_details(self, user_id):
        """Appelle le RPC GetUserDetail pour récupérer un seul utilisateur (pour l'édition)."""
        request = library_pb2.UserIdRequest(user_id=str(user_id))
        try:
            response = self.stub.GetUserDetail(request)
            if response and response.user_id:
                return response
            return None
        except grpc.RpcError as e:
            print(f"Error calling GetUserDetail RPC: {e.details()}")
            return None
            
    def delete_user(self, user_id):
        """Appelle le RPC DeleteUser pour désactiver un compte."""
        request = library_pb2.UserIdRequest(user_id=str(user_id))
        try:
            return self.stub.DeleteUser(request)
        except grpc.RpcError as e:
            details = e.details()
            return library_pb2.StatusResponse(success=False, message=f"Échec RPC: {details}")
        
   # --- GESTION DES CLIENTS ---
    
    def get_all_clients(self):
        request = library_pb2.SearchRequest(query="")
        try:
            return list(self.stub.GetAllClients(request))
        except grpc.RpcError:
            return []

    def get_client_details(self, client_id):
        """Récupère les détails d'un client par son ID pour l'édition."""
        request = library_pb2.ClientIdRequest(client_id=int(client_id))
        try:
            # On utilise GetClient (sans le "ById") pour correspondre au stub généré
            return self.stub.GetClient(request)
        except grpc.RpcError as e:
            print(f"Erreur gRPC GetClient: {e.details()}")
            return None
    def create_client(self, nom, email, telephone="", adresse=""):
        # Correction : library_pb2.Client
        request = library_pb2.Client(
            nom=nom,
            email=email,
            telephone=telephone,
            adresse=adresse
        )
        try:
            return self.stub.CreateClient(request)
        except grpc.RpcError as e:
            return library_pb2.StatusResponse(success=False, message=e.details())

    def update_client(self, client_id, nom, email, telephone, adresse):
    # On utilise le message Client défini dans votre .proto
        client_msg = library_pb2.Client(
            id=int(client_id),
            nom=nom,
            email=email,
            telephone=telephone,
            adresse=adresse
        )
        try:
            return self.stub.UpdateClient(client_msg)
        except grpc.RpcError as e:
            return library_pb2.StatusResponse(success=False, message=str(e.details()))
    def delete_client(self, client_id):
        # Correction : library_pb2.ClientIdRequest
        request = library_pb2.ClientIdRequest(client_id=int(client_id))
        try:
            return self.stub.DeleteClient(request)
        except grpc.RpcError as e:
            return library_pb2.ClientResponse(success=False, message=e.details())
        
####commendes#####
  # -------- EMPRUNTS (Loans) --------
    
    def create_loan(self, client_id, book_id, borrow_date=None, return_date=None):
        """Crée un nouvel emprunt."""
        borrow_date = borrow_date or datetime.now().strftime("%Y-%m-%d")
        return_date = return_date or (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        request = library_pb2.BorrowRequest(
            client_id=str(client_id),
            book_id=str(book_id),
            borrow_date=borrow_date,
            return_date=return_date
        )
        try:
            return self.stub.CreateLoan(request)
        except grpc.RpcError as e:
            return library_pb2.BorrowResponse(success=False, message=e.details())

    def get_loan(self, loan_id):
        """Récupère les détails d'un emprunt par ID."""
        request = library_pb2.BorrowListRequest(client_id=str(loan_id))
        try:
            return self.stub.GetLoan(request)
        except grpc.RpcError as e:
            print(f"Erreur gRPC GetLoan: {e.details()}")
            return None

    def list_loans(self, client_id=None):
        """Liste tous les emprunts ou ceux d’un client spécifique."""
        request = library_pb2.BorrowListRequest(client_id=str(client_id) if client_id else "")
        try:
            return list(self.stub.ListLoans(request))
        except grpc.RpcError as e:
            print(f"Erreur gRPC ListLoans: {e.details()}")
            return []

    def update_loan(self, loan_id, client_id, book_id, borrow_date, return_date):
        """Met à jour un emprunt existant."""
        request = library_pb2.BorrowRequest(
            client_id=str(client_id),
            book_id=str(book_id),
            borrow_date=borrow_date,
            return_date=return_date
        )
        try:
            return self.stub.UpdateLoan(request)
        except grpc.RpcError as e:
            return library_pb2.BorrowResponse(success=False, message=e.details())

    def return_book(self, loan_id):
        """Marque un livre comme retourné."""
        request = library_pb2.BorrowListRequest(client_id=str(loan_id))
        try:
            return self.stub.ReturnBook(request)
        except grpc.RpcError as e:
            return library_pb2.BorrowResponse(success=False, message=e.details())

    def get_loan_stats(self):
        """Récupère des statistiques globales des emprunts."""
        try:
            return self.stub.GetLoanStats(library_pb2.SearchRequest(query=""))
        except grpc.RpcError as e:
            print(f"Erreur gRPC GetLoanStats: {e.details()}")
            return None

    def get_available_books(self):
        """Liste les livres actuellement disponibles pour emprunt."""
        try:
            return list(self.stub.GetAvailableBooks(library_pb2.SearchRequest(query="")))
        except grpc.RpcError as e:
            print(f"Erreur gRPC GetAvailableBooks: {e.details()}")
            return []