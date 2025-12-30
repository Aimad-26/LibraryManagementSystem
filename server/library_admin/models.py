from django.db import models
from django.contrib.auth.models import User



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
    patron = models.ForeignKey(LibraryUser, on_delete=models.CASCADE)
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Loan of {self.book.title} to {self.patron.user.username}"
class Client(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom   