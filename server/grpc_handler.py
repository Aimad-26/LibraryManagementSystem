import os
import sys
import django
import grpc
from concurrent import futures
from django.db.models import Q

# ====================================================
# 1. DJANGO ENVIRONMENT SETUP
# ====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_server.settings")

try:
    django.setup()
    print("✅ Django initialisé avec library_server.settings")
except Exception as e:
    print(f"❌ Erreur Django setup: {e}")
    sys.exit(1)

# ====================================================
# 2. IMPORTS APRÈS django.setup()
# ====================================================

import library_pb2
import library_pb2_grpc

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, OperationalError

from library_admin.models import Book, Client as ClientModel

# ====================================================
# 3. gRPC SERVICER
# ====================================================

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):

    # ================= AUTH =================
    def UserLogin(self, request, context):
        user = authenticate(username=request.username, password=request.password)
        response = library_pb2.LoginResponse()

        if user and user.is_active and (user.is_staff or user.is_superuser):
            response.success = True
            response.user_id = str(user.id)
            response.message = f"Bienvenue {user.username}"
        else:
            response.success = False
            response.message = "Identifiants invalides"

        return response

    # ================= BOOK =================
    def CreateBook(self, request, context):
        try:
            total = request.total_copies if request.total_copies > 0 else 1
            book = Book.objects.create(
                title=request.title,
                author=request.author,
                isbn=request.isbn,
                total_copies=total,
                available_copies=total,
                image=request.image_url or None
            )
            return library_pb2.StatusResponse(
                success=True,
                message="Livre créé",
                entity_id=book.id
            )
        except IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            return library_pb2.StatusResponse(success=False, message="ISBN déjà existant")

    def SearchBooks(self, request, context):
        books = Book.objects.filter(
            Q(title__icontains=request.query) |
            Q(author__icontains=request.query)
        )
        for b in books:
            yield library_pb2.Book(
                id=b.id,
                title=b.title,
                author=b.author,
                isbn=b.isbn,
                total_copies=b.total_copies,
                available_copies=b.available_copies,
                image_url=str(b.image) if b.image else ""
            )

    # ================= USERS =================
    def GetAllUsers(self, request, context):
        users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        for u in users:
            yield library_pb2.UserDetail(
                user_id=str(u.id),
                username=u.username,
                email=u.email,
                is_staff=u.is_staff,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                date_joined=u.date_joined.isoformat()
            )

    def GetUserDetail(self, request, context):
        try:
            u = User.objects.get(id=int(request.user_id))
            return library_pb2.UserDetail(
                user_id=str(u.id),
                username=u.username,
                email=u.email,
                is_staff=u.is_staff,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                date_joined=u.date_joined.isoformat()
            )
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.UserDetail()

    def DeleteUser(self, request, context):
        try:
            u = User.objects.get(id=int(request.user_id))
            if u.is_superuser:
                context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                return library_pb2.StatusResponse(success=False, message="Interdit")
            u.delete()
            return library_pb2.StatusResponse(success=True, message="Utilisateur supprimé")
        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.StatusResponse(success=False, message="Utilisateur introuvable")

    # ================= CLIENTS =================
    def CreateClient(self, request, context):
        client = ClientModel.objects.create(
            nom=request.nom,
            email=request.email,
            telephone=request.telephone,
            adresse=request.adresse
        )
        return library_pb2.StatusResponse(
            success=True,
            message="Client créé",
            entity_id=client.id
        )

    from django.db.models import Q  # si tu utilises Django ORM pour la base de données

    def GetAllClients(self, request, context):
        for c in ClientModel.objects.all():
            yield library_pb2.Client(
                id=c.id,
                nom=c.nom,
                email=c.email,
                telephone=c.telephone,
                adresse=c.adresse,
                date_inscription=c.date_inscription.strftime("%d/%m/%Y")
            )

    def GetClient(self, request, context):
        try:
            c = ClientModel.objects.get(id=request.client_id)
            return library_pb2.Client(
                id=c.id,
                nom=c.nom,
                email=c.email,
                telephone=c.telephone,
                adresse=c.adresse,
                date_inscription=c.date_inscription.strftime("%d/%m/%Y")
            )
        except ClientModel.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.Client()

    def UpdateClient(self, request, context):
        try:
            client = ClientModel.objects.get(id=request.id)
            client.nom = request.nom
            client.email = request.email
            client.telephone = request.telephone
            client.adresse = request.adresse
            client.save()

            return library_pb2.StatusResponse(
                success=True,
                message="Client modifié",
                entity_id=client.id
            )
        except ClientModel.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.StatusResponse(success=False, message="Client introuvable")

    def DeleteClient(self, request, context):
        try:
            client = ClientModel.objects.get(id=request.client_id)
            client.delete()
            return library_pb2.StatusResponse(success=True, message="Client supprimé")
        except ClientModel.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return library_pb2.StatusResponse(success=False, message="Client introuvable")

# ====================================================
# 4. SERVER START
# ====================================================

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(
        LibraryServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("🚀 gRPC Server démarré sur le port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        Book.objects.exists()
        serve()
    except OperationalError:
        print("❌ Base de données indisponible")
