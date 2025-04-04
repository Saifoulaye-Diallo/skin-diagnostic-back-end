from django.db import models
from django.contrib.auth.models import User

class ImageDiagnostic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    image = models.ImageField(upload_to='diagnostic_images/')
    diagnostic_result = models.CharField(max_length=200)
    date_diagnostic = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.diagnostic_result} ({self.date_diagnostic.date()})"
