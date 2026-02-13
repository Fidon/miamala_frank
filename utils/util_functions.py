from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from dateutil.parser import parse, ParserError
from typing import Dict, Any, List, Optional
from django.http import HttpRequest
from django.db.models import QuerySet, Q, F
from django.db.models.functions import Lower


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


# --- DATABASE UTILITIES ---
def column_filtering(
    field_path: str, search_value: str, filter_kind: str = "contains"
) -> Optional[Q]:
    value = (search_value or "").strip()
    if not value:
        return None

    if filter_kind == "numeric":
        try:
            value = value.replace(',', '').strip()

            # Range: 100-200
            if '-' in value and not value.startswith('-') and not value.endswith('-'):
                start, end = value.split('-', 1)
                if (
                    start.replace('.', '', 1).isdigit()
                    and end.replace('.', '', 1).isdigit()
                ):
                    return Q(**{
                        f"{field_path}__gte": float(start),
                        f"{field_path}__lte": float(end),
                    })

            # <= value  (e.g. -100)
            if value.startswith('-') and value[1:].replace('.', '', 1).isdigit():
                return Q(**{f"{field_path}__lte": float(value[1:])})

            # >= value  (e.g. 100-)
            elif value.endswith('-') and value[:-1].replace('.', '', 1).isdigit():
                return Q(**{f"{field_path}__gte": float(value[:-1])})

            # Exact value
            elif value.replace('.', '', 1).isdigit():
                return Q(**{field_path: float(value)})

        except (ValueError, TypeError):
            return None
    elif filter_kind == "exact":
        if value.lower() in ['true', '1', 'yes']:
            filter_value = True
        elif value.lower() in ['false', '0', 'no']:
            filter_value = False
        else:
            filter_value = value
        return Q(**{field_path: filter_value})
    else:
        return Q(**{f"{field_path}__icontains": value})


class DataTableProcessor:
    """Core engine to handle DB-level DataTables operations with correct record counting"""
    
    @staticmethod
    def process_request(
        request: HttpRequest,
        queryset: QuerySet,
        global_search_fields: List[str],
        column_filter_fields: Dict[int, str],
        column_filter_types: Dict[str, str],
        column_sort_fields: Optional[Dict[int, str]] = None,
        date_field: str = 'created_at',
    ) -> Dict[str, Any]:
        if column_sort_fields is None:
            column_sort_fields = column_filter_fields

        total_records = queryset.count()

        draw = int(request.POST.get("draw", 1))
        start = int(request.POST.get("start", 0))
        length = int(request.POST.get("length", 10))
        global_search = (request.POST.get("search[value]", "") or "").strip()

        start_date = request.POST.get('startdate')
        end_date = request.POST.get('enddate')
        
        if start_date:
            try:
                queryset = queryset.filter(**{f"{date_field}__gte": parse(start_date)})
            except (ValueError, ParserError):
                pass
        if end_date:
            try:
                queryset = queryset.filter(**{f"{date_field}__lte": parse(end_date)})
            except (ValueError, ParserError):
                pass

        filtered_qs = queryset

        if global_search:
            q_global = Q()
            for field in global_search_fields:
                q_global |= Q(**{f"{field}__icontains": global_search})
            filtered_qs = filtered_qs.filter(q_global)

        for col_index, field_path in column_filter_fields.items():
            search_val = (request.POST.get(f"columns[{col_index}][search][value]", "") or "").strip()
            if search_val:
                filter_kind = column_filter_types.get(field_path, "contains")
                q_filter = column_filtering(field_path, search_val, filter_kind)
                if q_filter:
                    filtered_qs = filtered_qs.filter(q_filter)

        filtered_count = filtered_qs.count()

        order_idx = int(request.POST.get("order[0][column]", 2))
        order_dir = request.POST.get("order[0][dir]", "desc")
        sort_field = column_sort_fields.get(order_idx, "created_at")

        if sort_field in [date_field, 'created_at', 'updated_at'] or '__date' in sort_field:
            order_expr = F(sort_field).desc() if order_dir == "desc" else F(sort_field).asc()
        else:
            order_expr = Lower(sort_field).desc() if order_dir == "desc" else Lower(sort_field).asc()

        filtered_qs = filtered_qs.order_by(order_expr)

        paged_data = filtered_qs[start : start + length] if length > 0 else filtered_qs

        return {
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_count,
            "data": paged_data,
            "full_queryset": filtered_qs
        }
