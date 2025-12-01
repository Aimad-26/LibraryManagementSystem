from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200, help_text="Title of the book.")
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True, help_text="13-Digit ISBN.")
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"
