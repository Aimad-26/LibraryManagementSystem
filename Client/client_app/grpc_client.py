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
    def delete_member(self, m_id):
        return self.stub.DeleteMember(library_pb2.UserIdRequest(user_id=str(m_id)))
    def update_member(self, m_id, name, email, phone):
        req = library_pb2.Member(id=str(m_id), full_name=name, email=email, phone=phone)
        return self.stub.UpdateMember(req)
    def get_member_detail(self, m_id):
        return self.stub.GetMemberDetail(library_pb2.UserIdRequest(user_id=str(m_id)))
    def create_member(self, full_name, email, phone):
        req = library_pb2.Member(full_name=full_name, email=email, phone=phone)
        return self.stub.CreateMember(req)        
    def get_all_members(self):
        return list(self.stub.GetAllMembers(library_pb2.SearchRequest(query="")))
    #D2. Creation Wrapper (Uses update_staff_profile for detournement)
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
    def borrow_book(self, member_id, book_id):
        """Appelle le serveur pour enregistrer un emprunt."""
        request = library_pb2.BorrowRequest(
            member_id=str(member_id),
            book_id=int(book_id)
        )
        try:
            return self.stub.BorrowBook(request)
        except grpc.RpcError as e:
            print(f"Erreur gRPC : {e.details()}")
            return library_pb2.StatusResponse(success=False, message="Le serveur gRPC ne répond pas.")
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