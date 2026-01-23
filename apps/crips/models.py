from django.db import models
from apps.users.models import CustomUser

class Crips(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, verbose_name="Crips type", db_index=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, default=2, related_name='crips_user')
    comment = models.TextField(null=True, blank=True, default=None, verbose_name="Additional Notes")

    class Meta:
        indexes = [
            models.Index(fields=['name', 'created_at']),
        ]

    def __str__(self):
        return f"{self.name}"