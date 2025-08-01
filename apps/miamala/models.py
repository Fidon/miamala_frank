from django.db import models
from apps.shops.models import Shop
from apps.users.models import CustomUser

# selcomPay transactions model
class Selcompay(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(default='no-name', max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, default=2, related_name='sel_user')
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, default=1, related_name='sel_shop')

    def __str__(self):
        return str(self.amount)

# lipaNamba transactions model
class Lipanamba(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now=True)
    name = models.CharField(default='no-name', max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, default=2, related_name='lipa_user')
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, default=1, related_name='lipa_shop')

    def __str__(self):
        return str(self.amount)
    
# Debts transactions model
class Debts(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, default=2, related_name='debt_user')
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, default=1, related_name='debt_shop')

    def __str__(self):
        return str(self.name)
    
# Loans transactions model
class Loans(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, default=2, related_name='loan_user')
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, default=1, related_name='loan_shop')

    def __str__(self):
        return str(self.name)

# Expenses model
class Expenses(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now=True)
    dates = models.DateField()
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, default=None)
    deleted = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name='exp_user')
    shop = models.ForeignKey(Shop, on_delete=models.PROTECT, related_name='exp_shop')

    def __str__(self):
        return str(self.title)
