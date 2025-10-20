from django.db import models
from django.contrib.auth import get_user_model
from apps.produits.models import Produit

User = get_user_model()

class SearchEvent(models.Model):
    q = models.CharField(max_length=255)
    produit = models.ForeignKey(Produit, null=True, blank=True, on_delete=models.SET_NULL)
    utilisateur = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip_hash = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["produit", "created_at"]),
            models.Index(fields=["q", "created_at"]),
        ]
        ordering = ["-created_at"]
        db_table = "search_events"

    def __str__(self):
        return f"SearchEvent({self.q})"
