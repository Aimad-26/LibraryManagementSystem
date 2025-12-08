# In Client/client_app/grpc_client.py

import grpc
import sys
import os

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
    # C. Inventory Management (Create Book) 🚀 FINAL ADDITION 🚀
    # ----------------------------------------------------
    def create_book(self, title, author, isbn, total_copies, image_path=None):
        """Calls the remote CreateBook RPC on the server to add a new book."""
        
        # NOTE: Available copies is set on the server; we only pass the total.
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
    # D. Staff Management (Update Profile)
    # ----------------------------------------------------
    def update_staff_profile(self, staff_id, new_username, new_email, current_password, new_password=""):
        """
        Calls the remote UpdateStaffProfile RPC to change staff credentials.
        Returns a StatusResponse.
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
    # Dans client_app/grpc_client.py (Méthode à ajouter)

    def create_user(self, username, email, password):
    
    
    # staff_id est vide pour signaler au serveur que c'est une création
       return self.update_staff_profile(
        staff_id="", 
        new_username=username,
        new_email=email,
        current_password="", 
        new_password=password 
      )

# Note : Assurez-vous que votre méthode update_staff_profile existe et gère les arguments.