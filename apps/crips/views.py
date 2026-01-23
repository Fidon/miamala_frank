import logging
from typing import Dict, Any, List, Optional
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import QuerySet, Q, Sum, F, ExpressionWrapper, DecimalField
from django.urls import reverse
from dateutil.parser import parse
from decimal import Decimal

from .models import Crips
from utils.util_functions import admin_required, conv_timezone, format_number

logger = logging.getLogger(__name__)

# --- DATABASE SEARCH HELPER ---

def get_numeric_filter(field_name: str, search_value: str) -> Optional[Q]:
    """Translates numeric search syntax (-100, 100-, 100) into SQL Q objects"""
    try:
        val = search_value.replace(',', '').strip()
        if not val: return None
        if val.startswith('-') and val[1:].replace('.', '', 1).isdigit():
            return Q(**{f"{field_name}__lte": Decimal(val[1:])})
        elif val.endswith('-') and val[:-1].replace('.', '', 1).isdigit():
            return Q(**{f"{field_name}__gte": Decimal(val[:-1])})
        elif val.replace('.', '', 1).isdigit():
            return Q(**{field_name: Decimal(val)})
    except: pass
    return None

class DataTablesEngine:
    """Handles Database-level DataTables logic (Filtering, Sorting, Pagination)"""
    
    @staticmethod
    def handle_request(request: HttpRequest, queryset: QuerySet, 
                       search_fields: List[str], 
                       column_map: Dict[int, str],
                       numeric_fields: List[str] = None) -> Dict[str, Any]:
        
        records_total = queryset.count()
        
        # 1. Date Filtering
        start_date = request.POST.get('startdate')
        end_date = request.POST.get('enddate')
        if start_date:
            try: queryset = queryset.filter(created_at__gte=parse(start_date))
            except: pass
        if end_date:
            try: queryset = queryset.filter(created_at__lte=parse(end_date))
            except: pass

        # 2. Global Search
        search_val = request.POST.get('search[value]', '').strip()
        if search_val:
            q_obj = Q()
            for field in search_fields:
                q_obj |= Q(**{f"{field}__icontains": search_val})
            queryset = queryset.filter(q_obj)

        # 3. Individual Column Search
        for i in range(len(column_map)):
            col_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if col_search:
                field = column_map.get(i)
                if numeric_fields and field in numeric_fields:
                    num_q = get_numeric_filter(field, col_search)
                    if num_q: queryset = queryset.filter(num_q)
                else:
                    queryset = queryset.filter(**{f"{field}__icontains": col_search})

        records_filtered = queryset.count()

        # 4. Sorting
        order_idx = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')
        sort_field = column_map.get(order_idx, 'created_at')
        if order_dir == 'desc': sort_field = f"-{sort_field}"
        queryset = queryset.order_by(sort_field)

        # 5. Pagination
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        paged_data = queryset[start:start+length] if length > 0 else queryset
        
        return {
            'draw': int(request.POST.get('draw', 1)),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': paged_data,
            'full_queryset': queryset 
        }

# --- MANAGEMENT SERVICES ---

class CripsManagementService:
    """Service class for handling crips management operations"""

    @staticmethod
    def create_crip(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        """Create a new crip"""
        try:
            Crips.objects.create(
                name=post_data.get('name', '').strip(),
                qty=Decimal(post_data.get('qty', 0)),
                price=Decimal(post_data.get('price', 0)), user=user,
                comment=post_data.get('comment', '').strip() or None
            )
            return {'success': True, 'sms': 'Added successfully!'}
        except Exception as e:
            return {'success': False, 'sms': str(e)}

    @staticmethod
    def update_crip(post_data: Dict[str, Any], crip_id: int, user) -> Dict[str, Any]:
        """Update existing crip while avoiding duplicates"""
        try:
            item = Crips.objects.get(id=crip_id)
            item.name = post_data.get('name', '').strip()
            item.qty = Decimal(post_data.get('qty', 0))
            item.price = Decimal(post_data.get('price', 0))
            comment = post_data.get('comment', '').strip()
            item.comment = None if comment in ('N/A', "") else comment
            item.user = user
            item.save()
            return {'success': True, 'sms': 'Info updated successfully.'}
        except Crips.DoesNotExist:
            return {'success': False, 'sms': 'Crip not found.'}
        except Exception as e:
            return {'success': False, 'sms': str(e)}

    @staticmethod
    def get_crip_details(crip_id: int) -> Optional[Dict[str, Any]]:
        """Fetch formatted details for a single crip record"""
        try:
            crip = Crips.objects.get(id=crip_id)
            return {
                'id': crip.id,
                'regdate': conv_timezone(crip.created_at, '%d-%b-%Y %H:%M:%S'),
                'updated': conv_timezone(crip.updated_at, '%d-%b-%Y %H:%M:%S'),
                'name': crip.name,
                'price': crip.price,
                'qty': crip.qty,
                'price_txt': format_number(crip.price),
                'qty_txt': format_number(crip.qty),
                'comment': crip.comment or 'N/A',
                'types': ['Ndizi', 'Viazi', 'Tambi']
            }
        except Crips.DoesNotExist:
            return None

# --- VIEWS ---

@never_cache
@login_required
@admin_required()
def crips_page(request: HttpRequest) -> HttpResponse:
    """List view with DataTables support"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Crips.objects.annotate(
            amount=ExpressionWrapper(F('qty') * F('price'), output_field=DecimalField())
        ).select_related('user')
        
        cols = {0: 'id', 1: 'created_at', 2: 'name', 3: 'qty', 4: 'price', 5: 'amount', 6: 'user__username'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['name', 'user', 'comment'], cols, ['qty', 'price', 'amount'])
        
        grand_total = dt['full_queryset'].aggregate(total=Sum('amount'))['total'] or 0
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'regdate': conv_timezone(item.created_at, '%d-%b-%Y'),
            'name': item.name, 'qty': format_number(item.qty),
            'price': f"{format_number(item.price)} TZS", 'amount': f"{format_number(item.amount)} TZS",
            'user': item.user.username, 'info': reverse('crips_details', kwargs={'crip_id': item.id})
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'],
            'recordsTotal': dt['recordsTotal'],
            'recordsFiltered': dt['recordsFiltered'],
            'data': final_data,
            'grand_total': f"{format_number(grand_total)} TZS"
        })
        
    return render(request, 'crips/crips.html')

@never_cache
@login_required
@require_POST
@admin_required()
def crips_actions(request: HttpRequest) -> JsonResponse:
    """Action router for CRUD operations"""
    post = request.POST
    edit_id = post.get('edit_crips')
    del_id = post.get('delete_crips')
    
    if del_id:
        Crips.objects.filter(id=del_id).delete()
        return JsonResponse({'success': True, 'url': reverse('crips_page')})
    if edit_id:
        return JsonResponse(CripsManagementService.update_crip(post, edit_id, request.user))
    return JsonResponse(CripsManagementService.create_crip(post, request.user))

@never_cache
@login_required
@admin_required()
def crips_details(request: HttpRequest, crip_id: int) -> HttpResponse:
    """Detail view for a specific crip"""
    crip_data = CripsManagementService.get_crip_details(crip_id)
    if not crip_data:
        return redirect('crips_page')
    
    return render(request, 'crips/crips.html', {'crips_info': True, 'info': crip_data})