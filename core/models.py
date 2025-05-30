from django.db import models

class Transaction(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.price} грн ({self.category})"
