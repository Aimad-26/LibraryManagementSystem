from django.db import models

# Create your models here.
class Client(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.title
    
class Loan(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')  # NOUVEAU
    loan_date = models.DateTimeField(auto_now_add=True)  # Optionnel si pas déjà présent
    
    def __str__(self):
        return f"{self.client} - {self.book}"
