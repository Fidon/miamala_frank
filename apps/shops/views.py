import logging
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, F, Q, Count, Value, DecimalField, OuterRef, Subquery, QuerySet, Exists, Case, When, IntegerField
from django.db.models.functions import Coalesce, Lower, Concat
from django.utils import timezone
from dateutil.parser import parse
from decimal import Decimal
from typing import Dict, Any, List, Optional
from .forms import ShopForm, ShopUpdateForm, ProductForm, ProductUpdateForm
from .models import Shop, Product, Cart, Sales, Sale_items
from apps.users.models import CustomUser
from apps.miamala.models import Expenses, Debts, Loans, Selcompay, Lipanamba
from utils.util_functions import admin_required, conv_timezone, format_number

# Configure logging
logger = logging.getLogger(__name__)

def get_numeric_filter(field_name: str, search_value: str) -> Optional[Q]:
    """Database-level numeric filtering matching filter_items() logic"""
    try:
        search_value = search_value.replace(',', '').strip()
        if search_value.startswith('-') and search_value[1:].replace('.', '', 1).isdigit():
            return Q(**{f"{field_name}__lte": float(search_value[1:])})
        elif search_value.endswith('-') and search_value[:-1].replace('.', '', 1).isdigit():
            return Q(**{f"{field_name}__gte": float(search_value[:-1])})
        elif search_value.replace('.', '', 1).isdigit():
            return Q(**{field_name: float(search_value)})
    except (ValueError, TypeError):
        pass
    return None

# =============================================
# SHOP MANAGEMENT SERVICES
# =============================================
class ShopManagementService:
    """Service class for handling shop management operations"""

    @staticmethod
    def create_shop(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new shop with the provided data
        
        Args:
            post_data: Form data for shop creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            form = ShopForm(post_data)
            if form.is_valid():
                form.save()
                logger.info("New shop created successfully")
                return {'success': True, 'sms': 'New shop added successfully.'}
            
            error_msg = ShopManagementService._extract_form_error(form, ['names', 'abbrev', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error creating shop: {str(e)}")
            return {'success': False, 'sms': 'Failed to create shop. Please try again.'}

    @staticmethod
    def update_shop(post_data: Dict[str, Any], shop_id: int) -> Dict[str, Any]:
        """
        Update an existing shop with the provided data
        
        Args:
            post_data: Form data for shop update
            shop_id: ID of the shop to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            shop = Shop.objects.filter(pk=shop_id).first()
            if not shop:
                return {'success': False, 'sms': 'Shop not found.'}
            
            form = ShopUpdateForm(post_data, instance=shop)
            if form.is_valid():
                form.save()
                logger.info(f"Shop {shop_id} updated successfully")
                return {
                    'success': True,
                    'update_success': True,
                    'sms': 'Shop info updated successfully.'
                }
            
            error_msg = ShopManagementService._extract_form_error(form, ['names', 'abbrev', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error updating shop {shop_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update shop. Please try again.'}

    @staticmethod
    def delete_shop(shop_id: int) -> Dict[str, Any]:
        """
        Delete a shop
        
        Args:
            shop_id: ID of the shop to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            if shop_id == 1:
                return {'success': False, 'sms': 'Cannot delete the main shop.'}
            
            shop = Shop.objects.filter(pk=shop_id).first()
            if not shop:
                return {'success': False, 'sms': 'Operation failed.'}
            
            Expenses.objects.filter(shop=shop).delete()
            Loans.objects.filter(shop=shop).delete()
            Debts.objects.filter(shop=shop).delete()
            Lipanamba.objects.filter(shop=shop).delete()
            Selcompay.objects.filter(shop=shop).delete()
            shop.delete()
            logger.info(f"Shop {shop_id} deleted successfully")
            return {'success': True, 'url': reverse('shops_page')}
            
        except Exception as e:
            logger.error(f"Error deleting shop {shop_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed.'}

    @staticmethod
    def get_shop_details(shop_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a shop
        
        Args:
            shop_id: ID of the shop to get details for
            
        Returns:
            Dict containing shop details or None if not found
        """
        try:
            shop = Shop.objects.filter(pk=shop_id).first()
            if not shop:
                return None
            
            net_worth_subquery = Product.objects.filter(
                shop=OuterRef('pk'),
                is_deleted=False
            ).annotate(
                item_value=F('qty') * F('price')
            ).values('shop').annotate(
                total_value=Sum('item_value')
            ).values('total_value')[:1]
            
            shop_data = Shop.objects.filter(pk=shop_id).annotate(
                users_count=Count('users', filter=Q(users__deleted=False, users__is_admin=False)),
                items_count=Count('products', filter=Q(products__is_deleted=False)),
                networth=Coalesce(Subquery(net_worth_subquery), Value(0, output_field=DecimalField()))
            ).values('id', 'created_at', 'names', 'abbrev', 'comment', 'users_count', 'items_count', 'networth').first()
            
            if not shop_data:
                return None
            
            return {
                'id': shop_data['id'],
                'regdate': conv_timezone(shop_data['created_at'], '%d-%b-%Y %H:%M:%S'),
                'names': shop_data['names'],
                'abbrev': shop_data['abbrev'],
                'comment': shop_data['comment'] or 'N/A',
                'users_count': format_number(shop_data['users_count']),
                'items_count': format_number(shop_data['items_count']),
                'networth': format_number(shop_data['networth']),
                'delete_info': False if shop_data['id'] == 1 else True
            }
            
        except Exception as e:
            logger.error(f"Error getting shop details {shop_id}: {str(e)}")
            return None

    @staticmethod
    def _extract_form_error(form, field_names: List[str]) -> str:
        """Extract the first error message from specified form fields"""
        for field_name in field_names:
            if form.errors.get(field_name):
                return form.errors[field_name][0]
        return "Unknown error, reload & try again"

# =============================================
# PRODUCT MANAGEMENT SERVICES
# =============================================

class ProductManagementService:
    """Service class for handling product management operations"""

    @staticmethod
    def create_product(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product with the provided data
        
        Args:
            post_data: Form data for product creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            form = ProductForm(post_data)
            if form.is_valid():
                form.save()
                logger.info("New product created successfully")
                return {'success': True, 'sms': 'New item added successfully.'}
            
            error_msg = ProductManagementService._extract_form_error(
                form, ['name', 'qty', 'cost', 'price', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return {'success': False, 'sms': 'Failed to create product. Please try again.'}

    @staticmethod
    def update_product(post_data: Dict[str, Any], product_id: int) -> Dict[str, Any]:
        """
        Update an existing product with the provided data
        
        Args:
            post_data: Form data for product update
            product_id: ID of the product to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            product = Product.objects.filter(pk=product_id, is_deleted=False).first()
            if not product:
                return {'success': False, 'sms': 'Item not found.'}
            
            form = ProductUpdateForm(post_data, instance=product)
            if form.is_valid():
                form.save()
                logger.info(f"Product {product_id} updated successfully")
                return {
                    'success': True,
                    'update_success': True,
                    'sms': 'Item info updated successfully.'
                }
            
            error_msg = ProductManagementService._extract_form_error(
                form, ['name', 'qty', 'cost', 'price', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update product. Please try again.'}

    @staticmethod
    def delete_product(product_id: int) -> Dict[str, Any]:
        """
        Soft delete a product
        
        Args:
            product_id: ID of the product to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            product = Product.objects.filter(pk=product_id, is_deleted=False).first()
            if not product:
                return {'success': False, 'sms': 'Failed to delete product.'}
            
            product.is_deleted = True
            product.name = f"{product.name} (deleted)"
            product.save()
            logger.info(f"Product {product_id} deleted successfully")
            return {'success': True, 'url': reverse('products_page')}
            
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete product.'}

    @staticmethod
    def toggle_product_status(product_id: int) -> Dict[str, Any]:
        """
        Toggle product hidden/visible status
        
        Args:
            product_id: ID of the product to toggle
            
        Returns:
            Dict containing success status
        """
        try:
            product = Product.objects.filter(pk=product_id, is_deleted=False).first()
            if not product:
                return {'success': False, 'sms': 'Failed to block/unblock product.'}
            
            product.is_hidden = not product.is_hidden
            product.save()
            status = "blocked" if product.is_hidden else "unblocked"
            logger.info(f"Product {product_id} {status} successfully")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error toggling product status {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to block/unblock product.'}

    @staticmethod
    def update_product_quantity(product_id: int, new_qty: str) -> Dict[str, Any]:
        """
        Update product quantity
        
        Args:
            product_id: ID of the product to update
            new_qty: New quantity value
            
        Returns:
            Dict containing success status and message
        """
        try:
            qty_value = Decimal(new_qty)
            if qty_value < 1:
                return {'success': False, 'sms': 'Quantity must be at least 1.'}
            
            product = Product.objects.filter(pk=product_id, is_deleted=False).first()
            if not product:
                return {'success': False, 'sms': 'Failed to update quantity.'}
            
            product.qty = F('qty') + qty_value
            product.restock_date = timezone.now().date()
            product.save(update_fields=['qty', 'restock_date'])
            product.refresh_from_db()
            logger.info(f"Quantity updated for product {product_id}")
            return {'success': True, 'sms': 'Item stock updated.'}
            
        except Exception as e:
            logger.error(f"Error updating quantity for product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update quantity.'}

    @staticmethod
    def transfer_product(source_product_id: int, target_product_id: int, qty: Decimal) -> Dict[str, Any]:
        """
        Transfer product quantity between shops
        
        Args:
            source_product_id: ID of the source product
            target_product_id: ID of the target product
            qty: Quantity to transfer
            
        Returns:
            Dict containing success status and message
        """
        try:
            source_product = Product.objects.filter(pk=source_product_id, is_deleted=False).select_for_update().first()
            target_product = Product.objects.filter(pk=target_product_id, is_deleted=False).select_for_update().first()
            
            if not source_product or not target_product:
                return {'success': False, 'sms': 'Product not found.'}
            
            if source_product.qty < qty:
                return {'success': False, 'sms': 'Insufficient quantity in source shop.'}
            
            target_product.qty = F('qty') + qty
            target_product.restock_date = timezone.now().date()
            target_product.save(update_fields=['qty', 'restock_date'])
            
            source_product.qty = F('qty') - qty
            source_product.restock_date = timezone.now().date()
            source_product.save(update_fields=['qty', 'restock_date'])
            
            logger.info(f"Transferred {qty} from product {source_product_id} to {target_product_id}")
            return {
                'success': True,
                'sms': f"Transferred {qty} items from {source_product.shop.abbrev} to {target_product.shop.abbrev} successfully."
            }
            
        except Exception as e:
            logger.error(f"Error transferring product: {str(e)}")
            return {'success': False, 'sms': 'Failed to transfer product.'}

    @staticmethod
    def get_products_by_shop(shop_id: int) -> Dict[str, Any]:
        """
        Get all products for a specific shop
        
        Args:
            shop_id: ID of the shop
            
        Returns:
            Dict containing success status and products list
        """
        try:
            products = Product.objects.filter(shop_id=shop_id, is_deleted=False).values('id', 'name')
            return {'success': True, 'products': list(products)}
            
        except Exception as e:
            logger.error(f"Error getting products for shop {shop_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to retrieve products.'}
    
    @staticmethod
    def get_product_details(product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a product
        
        Args:
            product_id: ID of the product to get details for
            
        Returns:
            Dict containing product details or None if not found
        """
        try:
            sales_subquery = Sale_items.objects.filter(
                product=OuterRef('pk')
            ).annotate(
                sale_total=F('price') * F('qty')
            ).values('product').annotate(
                total_sales=Sum('sale_total')
            ).values('total_sales')[:1]
            
            product_data = Product.objects.filter(pk=product_id, is_deleted=False).annotate(
                sales_total=Coalesce(Subquery(sales_subquery), Value(0, output_field=DecimalField())),
                status_display=Case(
                    When(qty=0, then=Value('Sold Out')),
                    When(is_hidden=True, then=Value('Blocked')),
                    When(expiry_date__lte=timezone.now().date(), then=Value('Expired')),
                    default=Value('Available'),
                    output_field=models.CharField()
                )
            ).values(
                'id', 'created_at', 'updated_at', 'restock_date', 'shop_id',
                'name', 'cost', 'price', 'qty', 'is_hidden', 'expiry_date',
                'comment', 'sales_total', 'status_display'
            ).first()
            
            if not product_data:
                return None
            
            shop = Shop.objects.get(pk=product_data['shop_id'])
            
            return {
                'id': product_data['id'],
                'regdate': conv_timezone(product_data['created_at'], '%d-%b-%Y %H:%M:%S'),
                'lastupdated': conv_timezone(product_data['updated_at'], '%d-%b-%Y %H:%M:%S'),
                'restock': product_data['restock_date'].strftime('%d-%b-%Y'),
                'shop': shop,
                'name': product_data['name'],
                'cost': product_data['cost'],
                'price': product_data['price'],
                'qty': product_data['qty'],
                'cost_txt': format_number(product_data['cost']),
                'price_txt': format_number(product_data['price']),
                'qty_txt': format_number(product_data['qty']),
                'status': product_data['status_display'],
                'active': 'no' if product_data['is_hidden'] else 'yes',
                'expiry': product_data['expiry_date'],
                'expiry_date': product_data['expiry_date'].strftime('%d-%b-%Y') if product_data['expiry_date'] else "N/A",
                'comment': product_data['comment'] or 'N/A',
                'sales': format_number(product_data['sales_total']),
                'shops_list': Shop.objects.all().order_by('abbrev')
            }
            
        except Exception as e:
            logger.error(f"Error getting product details {product_id}: {str(e)}")
            return None

    @staticmethod
    def _extract_form_error(form, field_names: List[str]) -> str:
        """Extract the first error message from specified form fields"""
        for field_name in field_names:
            if form.errors.get(field_name):
                return form.errors[field_name][0]
        return "Unknown error, reload & try again"

# =============================================
# SALES MANAGEMENT SERVICES
# =============================================

class SalesManagementService:
    """Service class for handling sales operations"""

    @staticmethod
    def add_to_cart(request: HttpRequest, product_id: str, qty: str) -> Dict[str, Any]:
        """
        Add product to user's cart
        
        Args:
            request: HTTP request object
            product_id: ID of the product to add
            qty: Quantity to add
            
        Returns:
            Dict containing success status and message
        """
        try:
            product_qty = Decimal(qty)
            product = Product.objects.filter(pk=int(product_id), is_deleted=False).first()
            
            if not product:
                return {'success': False, 'sms': 'Product not found.'}
            
            if product_qty > product.qty:
                return {'success': False, 'sms': f'Qty exceeded available stock ({product.qty}).'}
            
            cart_item, created = Cart.objects.get_or_create(
                product=product,
                user=request.user,
                defaults={'qty': product_qty}
            )
            
            if not created:
                cart_item.qty = F('qty') + product_qty
                cart_item.save(update_fields=['qty'])
                cart_item.refresh_from_db()
            
            cart_count = Cart.objects.filter(user=request.user).count()
            cart_count_display = str(cart_count) if cart_count < 10 else '9+'
            
            logger.info(f"Added {product_qty} items to cart for user {request.user.id}")
            return {
                'success': True,
                'sms': f'{format_number(product_qty)} items added to cart.',
                'cart': cart_count_display
            }
            
        except Exception as e:
            logger.error(f"Error adding to cart for user {request.user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to add to cart.'}

    @staticmethod
    def delete_cart_item(cart_id: int, user: CustomUser) -> Dict[str, Any]:
        """
        Delete a cart item
        
        Args:
            cart_id: ID of the cart item to delete
            user: User object
            
        Returns:
            Dict containing success status and cart information
        """
        try:
            cart_item = Cart.objects.filter(id=cart_id, user=user).first()
            if not cart_item:
                return {'success': False, 'sms': 'Cart item not found.'}
            
            cart_item.delete()
            
            items_remaining = Cart.objects.filter(user=user).select_related('product')
            cart_count = items_remaining.count()
            cart_count_display = str(cart_count) if cart_count < 10 else '9+'
            
            grand_total = items_remaining.aggregate(
                total=Sum(F('product__price') * F('qty'))
            )['total'] or 0
            
            logger.info(f"Cart item {cart_id} deleted for user {user.id}")
            return {
                'success': True,
                'cart': cart_count_display,
                'grand_total': f"TZS. {format_number(grand_total)}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting cart item {cart_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete cart item.'}

    @staticmethod
    def clear_cart(user: CustomUser) -> Dict[str, Any]:
        """
        Clear all cart items for a user
        
        Args:
            user: User object
            
        Returns:
            Dict containing success status
        """
        try:
            Cart.objects.filter(user=user).delete()
            logger.info(f"Cart cleared for user {user.id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error clearing cart for user {user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to clear cart.'}

    @staticmethod
    def checkout(request: HttpRequest, customer: str, comment: str) -> Dict[str, Any]:
        """
        Process cart checkout
        
        Args:
            request: HTTP request object
            customer: Customer name
            comment: Sale comment
            
        Returns:
            Dict containing success status and message
        """
        try:
            full_cart = Cart.objects.filter(user=request.user).select_related('product', 'product__shop').select_for_update()
            if not full_cart:
                return {'success': False, 'sms': 'Cart is empty.'}
            
            cart_shops = set(item.product.shop for item in full_cart)
            if len(cart_shops) > 1:
                return {'success': False, 'sms': 'All products must be from the same shop to checkout.'}
            
            insufficient_stock = []
            for item in full_cart:
                if item.qty > item.product.qty:
                    insufficient_stock.append(item.product.name)
            
            if insufficient_stock:
                return {'success': False, 'sms': f'Not enough stock for: {", ".join(insufficient_stock)}'}
            
            cart_summary = full_cart.aggregate(
                grand_amount=Sum(F('product__price') * F('qty')),
                profit_count=Sum((F('product__price') - F('product__cost')) * F('qty'))
            )
            
            sale_transaction = Sales.objects.create(
                user=request.user,
                amount=cart_summary['grand_amount'] or 0,
                customer='n/a' if not customer.strip() else customer.strip(),
                comment=None if not comment.strip() else comment.strip(),
                shop=list(cart_shops)[0],
                profit=cart_summary['profit_count'] or 0
            )
            
            sale_items_batch = []
            product_updates = []
            
            for item in full_cart:
                sale_items_batch.append(Sale_items(
                    sale=sale_transaction,
                    product=item.product,
                    price=item.product.price,
                    qty=item.qty,
                    profit=(item.product.price - item.product.cost) * item.qty
                ))
                
                item.product.qty = F('qty') - item.qty
                product_updates.append(item.product)
            
            Sale_items.objects.bulk_create(sale_items_batch)
            
            Product.objects.bulk_update(product_updates, ['qty'])
            Cart.objects.filter(user=request.user).delete()
            
            logger.info(f"Checkout completed for user {request.user.id}")
            return {'success': True, 'sms': 'Checkout completed successfully!'}
            
        except Exception as e:
            logger.error(f"Error during checkout for user {request.user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to complete checkout.'}

    @staticmethod
    def remove_sale_item(item_id: int) -> Dict[str, Any]:
        """
        Remove an item from a sale and update related records
        
        Args:
            item_id: ID of the sale item to remove
            
        Returns:
            Dict containing success status and message
        """
        try:
            item = Sale_items.objects.select_related('sale', 'product').filter(id=item_id).select_for_update().first()
            if not item:
                return {'success': False, 'sms': 'Sale item not found.'}
            
            sale = item.sale
            product = item.product
            
            product.qty = F('qty') + item.qty
            product.save(update_fields=['qty'])
            
            sale.amount = F('amount') - (item.price * item.qty)
            sale.save(update_fields=['amount'])
            
            item.delete()
            
            has_remaining_items = Sale_items.objects.filter(sale=sale).exists()
            if not has_remaining_items:
                sale.delete()
                logger.info(f"Sale {sale.id} deleted as no items remain")
                return {'success': True, 'sales_page': reverse('sales_report'), 'items': 0}
            
            logger.info(f"Sale item {item_id} removed successfully")
            return {'success': True, 'sms': 'Item removed successfully.', 'items': 1}
            
        except Exception as e:
            logger.error(f"Error removing sale item {item_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to remove sale item.'}

    @staticmethod
    def delete_sale(sale_id: int) -> Dict[str, Any]:
        """
        Delete a sale and restore product quantities
        
        Args:
            sale_id: ID of the sale to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            sale = Sales.objects.filter(id=sale_id).first()
            if not sale:
                return {'success': False, 'sms': 'Sale not found.'}
            
            sale_items = Sale_items.objects.filter(sale=sale).select_related('product').select_for_update()
            
            product_updates = []
            for item in sale_items:
                item.product.qty = F('qty') + item.qty
                product_updates.append(item.product)
            
            Product.objects.bulk_update(product_updates, ['qty'])
            sale_items.delete()
            sale.delete()
            
            logger.info(f"Sale {sale_id} deleted successfully")
            return {'success': True, 'sales_page': reverse('sales_page')}
            
        except Exception as e:
            logger.error(f"Error deleting sale {sale_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete sale.'}

# =============================================
# DATATABLES ENGINE (OPTIMIZED)
# =============================================

class DataTablesEngine:
    """Core engine to handle DB-level DataTables operations with correct record counting"""
    
    @staticmethod
    def handle_request(request: HttpRequest, queryset: QuerySet, search_fields: List[str],
        column_map: Dict[int, str], numeric_fields: List[str] = None, date_field: str = 'created_at',
        user_shop_filter: bool = False, user=None) -> Dict[str, Any]:
        
        if user_shop_filter and user and not user.is_admin:
            queryset = queryset.filter(shop=user.shop)
        
        records_total = queryset.count()
        
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_val = request.POST.get('search[value]', '').strip()
        
        start_date = request.POST.get('startdate')
        end_date = request.POST.get('enddate')
        
        if start_date:
            try:
                queryset = queryset.filter(**{f"{date_field}__gte": parse(start_date)})
            except:
                pass
        if end_date:
            try:
                queryset = queryset.filter(**{f"{date_field}__lte": parse(end_date)})
            except:
                pass
        
        if search_val:
            q_obj = Q()
            for field in search_fields:
                q_obj |= Q(**{f"{field}__icontains": search_val})
            queryset = queryset.filter(q_obj)
        
        for i in range(len(column_map)):
            col_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if col_search:
                field = column_map.get(i)
                if numeric_fields and field in numeric_fields:
                    num_q = get_numeric_filter(field, col_search)
                    if num_q:
                        queryset = queryset.filter(num_q)
                else:
                    queryset = queryset.filter(**{f"{field}__icontains": col_search})
        
        records_filtered = queryset.count()
        
        order_idx = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')
        sort_field = column_map.get(order_idx, date_field)
        if (numeric_fields and sort_field in numeric_fields) or sort_field == date_field:
            ordering = sort_field
            if order_dir == 'desc':
                ordering = f"-{sort_field}"
            queryset = queryset.order_by(ordering)
        else:
            sort_expression = Lower(sort_field)
            if order_dir == 'desc':
                queryset = queryset.order_by(sort_expression.desc())
            else:
                queryset = queryset.order_by(sort_expression.asc())
        
        paged_data = queryset[start:start+length] if length > 0 else queryset
        
        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': paged_data,
            'full_queryset': queryset
        }

# =============================================
# DATATABLES SERVICES (OPTIMIZED)
# =============================================

class ShopDataTablesService:
    """Service class for handling shop DataTables functionality"""

    @staticmethod
    def handle_request(request: HttpRequest) -> JsonResponse:
        try:
            queryset = Shop.objects.all().annotate(
                users_count=Count('users', filter=Q(users__deleted=False, users__is_admin=False)),
                items_count=Count('products', filter=Q(products__is_deleted=False)),
                networth=Coalesce(
                    Sum(F('products__qty') * F('products__price'), filter=Q(products__is_deleted=False)),
                    Value(0, output_field=DecimalField())
                )
            )
            
            dt_result = DataTablesEngine.handle_request(
                request=request,
                queryset=queryset,
                search_fields=['names', 'abbrev'],
                column_map={0: 'id', 1: 'names', 2: 'abbrev', 3: 'created_at', 4: 'users_count', 5: 'items_count', 6: 'networth'},
                numeric_fields=['users_count', 'items_count', 'networth']
            )
            
            final_data = []
            for i, item in enumerate(dt_result['data']):
                final_data.append({
                    'count': int(request.POST.get('start', 0)) + i + 1,
                    'id': item.id,
                    'regdate': conv_timezone(item.created_at, '%d-%b-%Y'),
                    'names': item.names,
                    'abbrev': item.abbrev,
                    'users_count': format_number(item.users_count),
                    'items_count': format_number(item.items_count),
                    'networth': format_number(item.networth) + " TZS",
                    'info': reverse('shop_details', kwargs={'shopid': item.id})
                })
            
            return JsonResponse({
                'draw': dt_result['draw'],
                'recordsTotal': dt_result['recordsTotal'],
                'recordsFiltered': dt_result['recordsFiltered'],
                'data': final_data
            })
            
        except Exception as e:
            logger.error(f"Error in ShopDataTablesService: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })

class ProductDataTablesService:
    """Service class for handling product DataTables functionality"""

    @staticmethod
    def handle_request(request: HttpRequest) -> JsonResponse:
        try:
            queryset = Product.objects.filter(is_deleted=False).select_related('shop').annotate(
                status_display=Case(
                    When(qty=0, then=Value('SoldOut')),
                    When(is_hidden=True, then=Value('Blocked')),
                    When(expiry_date__lte=timezone.now().date(), then=Value('Expired')),
                    default=Value('Active'),
                    output_field=models.CharField()
                )
            )
            
            if not request.user.is_admin:
                queryset = queryset.filter(shop=request.user.shop)
            
            dt_result = DataTablesEngine.handle_request(
                request=request,
                queryset=queryset,
                search_fields=['name', 'shop__abbrev'],
                column_map={0: 'id', 1: 'name', 2: 'shop__abbrev', 3: 'qty', 4: 'cost', 5: 'price', 6: 'status_display'},
                numeric_fields=['qty', 'cost', 'price'],
                user_shop_filter=False,
                user=request.user
            )
            
            final_data = []
            for i, item in enumerate(dt_result['data']):
                final_data.append({
                    'count': int(request.POST.get('start', 0)) + i + 1,
                    'id': item.id,
                    'name': item.name,
                    'shop': item.shop.abbrev,
                    'qty': format_number(item.qty),
                    'cost': format_number(item.cost) + " TZS",
                    'price': format_number(item.price) + " TZS",
                    'status': item.status_display,
                    'info': reverse('product_details', kwargs={'itemid': item.id})
                })
            
            return JsonResponse({
                'draw': dt_result['draw'],
                'recordsTotal': dt_result['recordsTotal'],
                'recordsFiltered': dt_result['recordsFiltered'],
                'data': final_data
            })
            
        except Exception as e:
            logger.error(f"Error in ProductDataTablesService: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })

class SalesDataTablesService:
    """Service class for handling sales DataTables functionality"""

    @staticmethod
    def handle_request(request: HttpRequest) -> JsonResponse:
        try:
            queryset = Product.objects.filter(
                is_deleted=False, 
                is_hidden=False, 
                qty__gt=0
            ).select_related('shop')
            
            if not request.user.is_admin:
                queryset = queryset.filter(shop=request.user.shop)
            
            cart_subquery = Cart.objects.filter(
                user=request.user,
                product=OuterRef('pk')
            ).values('qty')[:1]
            
            queryset = queryset.annotate(
                cart_qty=Coalesce(Subquery(cart_subquery), Value(0, output_field=DecimalField()))
            )
            
            dt_result = DataTablesEngine.handle_request(
                request=request,
                queryset=queryset,
                search_fields=['name'],
                column_map={0: 'id', 1: 'name', 2: 'qty', 3: 'price'},
                numeric_fields=['qty', 'price'],
                user_shop_filter=False,
                user=request.user
            )
            
            final_data = []
            for i, item in enumerate(dt_result['data']):
                final_data.append({
                    'count': int(request.POST.get('start', 0)) + i + 1,
                    'id': item.id,
                    'name': item.name,
                    'qty': format_number(item.qty),
                    'price': format_number(item.price) + " TZS",
                    'sell_qty': format_number(item.qty),
                    'cart': format_number(item.cart_qty),
                    'action': ''
                })
            
            return JsonResponse({
                'draw': dt_result['draw'],
                'recordsTotal': dt_result['recordsTotal'],
                'recordsFiltered': dt_result['recordsFiltered'],
                'data': final_data
            })
            
        except Exception as e:
            logger.error(f"Error in SalesDataTablesService: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })

class SalesReportDataTablesService:
    """Service class for handling sales report DataTables functionality"""

    @staticmethod
    def handle_request(request: HttpRequest) -> JsonResponse:
        try:
            queryset = Sales.objects.all().select_related('shop', 'user')
            
            dt_result = DataTablesEngine.handle_request(
                request=request,
                queryset=queryset,
                search_fields=['customer', 'user__username', 'shop__abbrev'],
                column_map={0: 'sales_items', 1: 'id', 2: 'created_at', 3: 'shop__abbrev', 4: 'amount', 5: 'profit', 6: 'customer', 7: 'user__username'},
                numeric_fields=['amount', 'profit'],
                user_shop_filter=True,
                user=request.user
            )
            
            sale_ids = [sale.id for sale in dt_result['data']]
            sale_items_map = {}
            if sale_ids:
                items = Sale_items.objects.filter(sale_id__in=sale_ids).select_related('product')
                for item in items:
                    sale_items_map.setdefault(item.sale_id, []).append({
                        'count': len(sale_items_map.get(item.sale_id, [])) + 1,
                        'names': item.product.name,
                        'price': format_number(item.price) + " TZS",
                        'qty': format_number(item.qty),
                        'total': format_number(item.price * item.qty) + " TZS"
                    })
            
            final_data = []
            for i, sale in enumerate(dt_result['data']):
                final_data.append({
                    'count': int(request.POST.get('start', 0)) + i + 1,
                    'id': sale.id,
                    'saledate': conv_timezone(sale.created_at, '%d-%b-%Y %H:%M:%S'),
                    'shop': sale.shop.abbrev,
                    'user': sale.user.username if not sale.user.deleted else f"{sale.user.username} (deleted)",
                    'customer': sale.customer,
                    'amount': format_number(sale.amount) + " TZS",
                    'profit': format_number(sale.profit) + " TZS",
                    'items': sale_items_map.get(sale.id, [])
                })
            
            totals = dt_result['full_queryset'].aggregate(
                total_amount=Sum('amount'),
                total_profit=Sum('profit')
            )
            
            return JsonResponse({
                'draw': dt_result['draw'],
                'recordsTotal': dt_result['recordsTotal'],
                'recordsFiltered': dt_result['recordsFiltered'],
                'data': final_data,
                'grand_total': format_number(totals['total_amount'] or 0) + " TZS",
                'grand_profit': format_number(totals['total_profit'] or 0) + " TZS"
            })
            
        except Exception as e:
            logger.error(f"Error in SalesReportDataTablesService: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })

class SalesItemsReportDataTablesService:
    """Service class for handling sales items report DataTables functionality"""

    @staticmethod
    def handle_request(request: HttpRequest) -> JsonResponse:
        try:
            queryset = Sale_items.objects.all().select_related(
                'sale', 'sale__shop', 'sale__user', 'product'
            ).annotate(
                amount_total=F('price') * F('qty'),
                user_display=Case(
                    When(sale__user__deleted=True, then=Concat(F('sale__user__username'), Value(' (deleted)'))),
                    default=F('sale__user__username'),
                    output_field=models.CharField()
                )
            )
            
            dt_result = DataTablesEngine.handle_request(
                request=request,
                queryset=queryset,
                search_fields=['product__name', 'sale__shop__abbrev', 'sale__user__username'],
                column_map={0: 'id', 1: 'sale__created_at', 2: 'sale__shop__abbrev', 3: 'product__name', 
                          4: 'price', 5: 'qty', 6: 'amount_total', 7: 'profit', 8: 'user_display'},
                numeric_fields=['price', 'qty', 'amount_total', 'profit'],
                date_field='sale__created_at',
                user_shop_filter=True,
                user=request.user
            )
            
            final_data = []
            for i, item in enumerate(dt_result['data']):
                final_data.append({
                    'count': int(request.POST.get('start', 0)) + i + 1,
                    'id': item.id,
                    'saledate': conv_timezone(item.sale.created_at, '%d-%b-%Y %H:%M:%S'),
                    'shop': item.sale.shop.abbrev,
                    'product': item.product.name,
                    'price': format_number(item.price) + " TZS",
                    'qty': format_number(item.qty),
                    'amount': format_number(item.amount_total) + " TZS",
                    'profit': format_number(item.profit) + " TZS",
                    'user': item.user_display
                })
            
            totals = dt_result['full_queryset'].aggregate(
                total_amount=Sum('amount_total'),
                total_profit=Sum('profit')
            )
            
            return JsonResponse({
                'draw': dt_result['draw'],
                'recordsTotal': dt_result['recordsTotal'],
                'recordsFiltered': dt_result['recordsFiltered'],
                'data': final_data,
                'grand_total': format_number(totals['total_amount'] or 0) + " TZS",
                'grand_profit': format_number(totals['total_profit'] or 0) + " TZS"
            })
            
        except Exception as e:
            logger.error(f"Error in SalesItemsReportDataTablesService: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })

# =============================================
# VIEW FUNCTIONS
# =============================================

@never_cache
@login_required
@require_POST
@admin_required()
def shops_requests(request: HttpRequest) -> JsonResponse:
    """
    Handle various shop management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        edit_shop = post_data.get('edit_shop')
        delete_shop = post_data.get('delete_shop')
        
        if delete_shop:
            result = ShopManagementService.delete_shop(int(delete_shop))
        elif edit_shop:
            result = ShopManagementService.update_shop(post_data, int(edit_shop))
        else:
            result = ShopManagementService.create_shop(post_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in shops_requests: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
@admin_required()
def shops_page(request: HttpRequest) -> HttpResponse:
    """
    Handle shops page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        return ShopDataTablesService.handle_request(request)
    
    return render(request, 'shops/shops.html', {'shops': Shop.objects.all().order_by('-created_at')})

@never_cache
@login_required
@admin_required()
@require_GET
def shop_details(request: HttpRequest, shopid: int) -> HttpResponse:
    """
    Display detailed shop information page
    
    Args:
        request: HTTP request object
        shopid: ID of the shop to display
        
    Returns:
        Rendered template or redirect
    """
    try:
        shop_data = ShopManagementService.get_shop_details(shopid)
        if not shop_data:
            return redirect('shops_page')
        
        return render(request, 'shops/shops.html', {
            'shopinfo': shopid,
            'info': shop_data,
            'delete_info': shop_data['delete_info']
        })
        
    except Exception as e:
        logger.error(f"Error in shop_details for shop {shopid}: {str(e)}")
        return redirect('shops_page')

@never_cache
@login_required
def products_page(request: HttpRequest) -> HttpResponse:
    """
    Handle products page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        return ProductDataTablesService.handle_request(request)
    
    return render(request, 'shops/products.html', {'shops': Shop.objects.all().order_by('-created_at')})

@never_cache
@login_required
@require_POST
def products_requests(request: HttpRequest) -> JsonResponse:
    """
    Handle various product management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        edit_product = post_data.get('edit_product')
        delete_product = post_data.get('delete_product')
        block_product = post_data.get('block_product')
        qty_product = post_data.get('qty_product')
        new_qty = post_data.get('qty_new')
        trf_shop = post_data.get('transfer_shop')
        trf_product = post_data.get('transfer_product')
        
        if qty_product and new_qty:
            result = ProductManagementService.update_product_quantity(int(qty_product), new_qty)
        elif block_product:
            result = ProductManagementService.toggle_product_status(int(block_product))
        elif delete_product:
            result = ProductManagementService.delete_product(int(delete_product))
        elif edit_product:
            result = ProductManagementService.update_product(post_data, int(edit_product))
        elif trf_shop:
            result = ProductManagementService.get_products_by_shop(int(trf_shop))
        elif trf_product:
            child_id = int(post_data.get('product'))
            qty = Decimal(post_data.get('qty'))
            result = ProductManagementService.transfer_product(int(trf_product), child_id, qty)
        else:
            result = ProductManagementService.create_product(post_data)
        
        return JsonResponse(result)
    
    except Exception as e:
        logger.error(f"Error in products_requests: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
@require_GET
def product_details(request: HttpRequest, itemid: int) -> HttpResponse:
    """
    Display detailed product information page
    
    Args:
        request: HTTP request object
        itemid: ID of the product to display
        
    Returns:
        Rendered template or redirect
    """
    try:
        product_data = ProductManagementService.get_product_details(itemid)
        if not product_data:
            return redirect('products_page')
        
        return render(request, 'shops/products.html', {
            'productinfo': True,
            'info': product_data
        })
        
    except Exception as e:
        logger.error(f"Error in product_details for product {itemid}: {str(e)}")
        return redirect('products_page')

@never_cache
@login_required
def sales_page(request: HttpRequest) -> HttpResponse:
    """
    Handle sales page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        return SalesDataTablesService.handle_request(request)
    
    cart = Cart.objects.filter(user=request.user).select_related('product').order_by('id')
    grand_total = cart.aggregate(
        total=Sum(F('product__price') * F('qty'))
    )['total'] or 0
    
    cart_items = [
        {
            'id': item.id,
            'name': item.product.name,
            'price': f"TZS. {format_number(item.product.price)}",
            'qty': format_number(item.qty),
            'max_qty': item.product.qty
        }
        for item in cart
    ]
    
    context = {
        'cart_label': str(cart.count()) if cart.count() < 10 else '9+',
        'cart_count': cart.count(),
        'cart_items': cart_items,
        'total': f"TZS. {format_number(grand_total)}"
    }
    return render(request, 'shops/sales.html', context)

@never_cache
@login_required
@require_POST
def sales_actions(request: HttpRequest) -> JsonResponse:
    """
    Handle various sales-related actions via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        add_to_cart = post_data.get('cart_add')
        cart_delete = post_data.get('cart_delete')
        clear_cart = post_data.get('clear_cart')
        checkout = post_data.get('checkout')
        item_remove = post_data.get('item_remove')
        sales_delete = post_data.get('sales_delete')
        
        if add_to_cart:
            result = SalesManagementService.add_to_cart(
                request, post_data.get('product'), post_data.get('qty'))
        elif cart_delete:
            result = SalesManagementService.delete_cart_item(int(cart_delete), request.user)
        elif clear_cart:
            result = SalesManagementService.clear_cart(request.user)
        elif checkout:
            result = SalesManagementService.checkout(
                request, post_data.get('customer'), post_data.get('comment'))
        elif item_remove:
            result = SalesManagementService.remove_sale_item(int(item_remove))
        elif sales_delete:
            result = SalesManagementService.delete_sale(int(sales_delete))
        else:
            result = {'success': False, 'sms': 'Invalid action.'}
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in sales_actions: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
def sales_report(request: HttpRequest) -> HttpResponse:
    """
    Handle sales report page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        return SalesReportDataTablesService.handle_request(request)
    
    shops = Shop.objects.all() if request.user.is_admin else Shop.objects.filter(id=request.user.shop_id)
    return render(request, 'shops/sales_report.html', {'shops': shops.order_by('-created_at')})

@never_cache
@login_required
def sales_items_report(request: HttpRequest) -> HttpResponse:
    """
    Handle sales items report page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        return SalesItemsReportDataTablesService.handle_request(request)
    
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'shops/items_report.html', {'shops': shops})
