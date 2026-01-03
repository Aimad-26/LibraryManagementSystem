from django.db import models
import uuid
from django.contrib.auth.models import User

class Member(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="Nom Complet")
    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    # On ajoute blank=True pour que Django accepte de ne pas le remplir dans les formulaires/gRPC
    member_id = models.CharField(max_length=50, unique=True, blank=True, verbose_name="ID Membre")
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_loans = models.IntegerField(default=5, verbose_name="Nombre maximum de prêts")

    def save(self, *args, **kwargs):
        # Si le member_id est vide (chaîne vide ou None)
        if not self.member_id:
            # Génère un identifiant unique type MEM-XXXXXX
            self.member_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        super(Member, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.member_id})"

class Book(models.Model):
    title = models.CharField(max_length=200, help_text="Title of the book.")
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True, help_text="13-Digit ISBN.")
    total_copies = models.IntegerField(default=1, help_text="Total number of copies owned.")
    available_copies = models.IntegerField(default=1, 
                                           help_text="Number of copies currently available for loan.") # <-- SYNTAX FIX: Added closing parenthesis
    image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} by {self.author} (Available: {self.available_copies}/{self.total_copies})"
    
class LibraryUser(models.Model):
    # Links to the built-in Django User model for authentication if needed for a separate login.
    # For now, it simply uses the existing primary User table for ID/name storage.
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    
    # Custom, permanent ID for the patron (will be used as the gRPC identifier/token)
    member_id = models.CharField(max_length=20, unique=True, verbose_name="Library Member ID")
    max_loans = models.IntegerField(default=5)

    def __str__(self):
        return f"Patron: {self.user.username} ({self.member_id})"

class Loan(models.Model):
   book = models.ForeignKey(Book, on_delete=models.CASCADE)
    # Ajoutez null=True, blank=True temporairement
   member = models.ForeignKey(Member, on_delete=models.CASCADE, null=True, blank=True)
   loan_date = models.DateField(auto_now_add=True)
   due_date = models.DateField()
   returned_date = models.DateField(null=True, blank=True)

   def save(self, *args, **kwargs):
        # Définit automatiquement une date de retour à +14 jours si non spécifiée
        if not self.due_date:
            self.due_date = timezone.now().date() + timedelta(days=14)
        super().save(*args, **kwargs)

   def __str__(self):
        return f"Loan: {self.book.title} -> {self.member.full_name}"