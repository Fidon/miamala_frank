from django.db import models
from django.utils import timezone

# shop model
class Shop(models.Model):
    names = models.CharField(max_length=255, verbose_name="Shop Name", db_index=True)
    abbrev = models.CharField(max_length=50, unique=True, verbose_name="Abbreviation", db_index=True)
    comment = models.TextField(blank=True, null=True, verbose_name="Comments")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At", db_index=True)

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"
        ordering = ['names']

    def __str__(self):
        return self.abbrev

# shop item model
class Product(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products', db_index=True)
    name = models.CharField(max_length=255, verbose_name="Product Name", db_index=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Price")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Selling Price")
    is_hidden = models.BooleanField(default=False, verbose_name="Temporarily Unavailable", db_index=True)
    is_deleted = models.BooleanField(default=False, verbose_name="Deleted", db_index=True)
    restock_date = models.DateField(default=timezone.now, verbose_name="Last Restock Date", db_index=True)
    expiry_date = models.DateField(null=True, blank=True, default=None, verbose_name="Expiry Date", db_index=True)
    comment = models.TextField(null=True, blank=True, default=None, verbose_name="Additional Notes")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.shop.name})"

# Cart model
class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items', db_index=True)
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantity")
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT, related_name='cart_users', db_index=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ['-qty']

    def __str__(self):
        return str(self.product)

# Sales model
class Sales(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT, related_name='sales_user', db_index=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='shop_sale', db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale amount")
    profit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Profit")
    customer = models.CharField(max_length=255, default='n/a', verbose_name="Customer name")
    comment = models.TextField(null=True, blank=True, default=None)

    class Meta:
        indexes = [
            models.Index(fields=['-created_at', 'shop']),
        ]

    def __str__(self):
        return str(self.amount)

# Sales_items model
class Sale_items(models.Model):
    id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='sales', db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sale_product', db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Item price")
    qty = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Item qty")
    profit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sale profit")

    class Meta:
        indexes = [
            models.Index(fields=['sale', 'product']),
        ]

    def __str__(self):
        return str(self.product)