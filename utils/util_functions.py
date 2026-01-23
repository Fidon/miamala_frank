from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


# Decorator to check if the user is an admin
def admin_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated and user.is_admin:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


# Format phone number to a standard format
def format_phone(phone):
    if not phone:
        return "N/A"
    if len(phone) >= 13:
        return f"{phone[:4]} {phone[4:7]} {phone[7:10]} {phone[10:]}"
    return phone


# convert datetime to local timezone and format it
def conv_timezone(dt, dt_format):
    dtime = timezone.localtime(dt)
    return dtime.strftime(dt_format)


# Filter items based on table columns
def filter_items(column_field, column_search, item, filter_type):
    column_value = str(item.get(column_field, '')).lower()
    column_search_lower = column_search.lower()

    if filter_type == 'exact':
        return column_search_lower == column_value
    
    elif filter_type == 'numeric':
        try:
            item_value = float(column_value) if column_value else 0.0
            if column_search.startswith('-') and column_search[1:].replace(',', '').isdigit():
                max_value = float(column_search[1:].replace(',', ''))
                return item_value <= max_value
            elif column_search.endswith('-') and column_search[:-1].replace(',', '').isdigit():
                min_value = float(column_search[:-1].replace(',', ''))
                return item_value >= min_value
            elif column_search.replace(',', '').replace('.', '', 1).isdigit(): # Allow floats like "123.45"
                target_value = float(column_search.replace(',', ''))
                return item_value == target_value
        except ValueError:
            return False
    return column_search_lower in column_value


def format_number(value):
    value = Decimal(value)
    if value == value.to_integral():
        return f"{int(value):,}"
    elif value * 10 == int(value * 10):
        return f"{value:.1f}".rstrip('0').rstrip('.')
    else:
        return f"{value:.2f}".rstrip('0').rstrip('.')
    

# selcomPay profit calculation per transaction
def selcom_profit(amount):
    amount = Decimal(str(amount))
    charge_ranges = {
        (Decimal('1000'), Decimal('4999')): Decimal('400'),
        (Decimal('5000'), Decimal('9999')): Decimal('800'),
        (Decimal('10000'), Decimal('19999')): Decimal('1000'),
        (Decimal('20000'), Decimal('39999')): Decimal('1500'),
        (Decimal('40000'), Decimal('49999')): Decimal('2000'),
        (Decimal('50000'), Decimal('99999')): Decimal('2500'),
        (Decimal('100000'), Decimal('199999')): Decimal('3300'),
        (Decimal('200000'), Decimal('299999')): Decimal('4500'),
    }
    percentage_fee = Decimal('0.013')
    for (lower, upper), charge in charge_ranges.items():
        if lower <= amount <= upper:
            profit = abs((amount * percentage_fee) - charge)
            return profit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal('0.00')

# Lipanamba profit calculation per transaction
def lipa_profit(amount):
    amount = Decimal(str(amount))
    charge_ranges = {
        (Decimal('1000'), Decimal('4999')): Decimal('300.00'),
        (Decimal('5000'), Decimal('19999')): Decimal('500.00'),
        (Decimal('20000'), Decimal('49999')): Decimal('800.00'),
        (Decimal('50000'), Decimal('99999')): Decimal('1000.00'),
        (Decimal('100000'), Decimal('199999')): Decimal('1500.00'),
        (Decimal('200000'), Decimal('299999')): Decimal('2000.00'),
        (Decimal('300000'), Decimal('1000000')): Decimal('2500.00'),
    }
    for (lower, upper), charge in charge_ranges.items():
        if lower <= amount <= upper:
            return charge
    return Decimal('0.00')
