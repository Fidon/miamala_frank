import logging
from typing import Dict, Any, Optional
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.urls import reverse
from decimal import Decimal

from .models import Crips
from apps.users.models import CustomUser
from utils.util_functions import admin_required, conv_timezone, format_number, DataTableProcessor

logger = logging.getLogger(__name__)

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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Crips.objects.annotate(
            amount=ExpressionWrapper(F('qty') * F('price'), output_field=DecimalField())
        ).select_related('user')
        
        column_filter_fields = {
            1: "created_at",
            2: "name",
            3: "qty",
            4: "price",
            5: "amount",
            6: "user__username",
        }
        column_sort_fields = column_filter_fields.copy()
        column_filter_types = {
            "name": "contains",
            "qty": "numeric",
            "price": "numeric",
            "amount": "numeric",
            "user__username": "exact",
        }
        global_search = [
            "name", "qty", "price", "amount", "user__username", "user__fullname"
            ]

        result = DataTableProcessor.process_request(
            request=request,
            queryset=qs,
            global_search_fields=global_search,
            column_filter_fields=column_filter_fields,
            column_filter_types=column_filter_types,
            column_sort_fields=column_sort_fields,
            date_field='created_at',
        )

        grand_total = result['full_queryset'].aggregate(total=Sum('amount'))['total'] or 0

        start_idx = int(request.POST.get("start", 0))

        final_data = [{
            'count': start_idx + i + 1,
            'id': item.id, 'regdate': conv_timezone(item.created_at, '%d-%b-%Y'),
            'name': item.name, 'qty': format_number(item.qty),
            'price': f"{format_number(item.price)} TZS", 'amount': f"{format_number(item.amount)} TZS",
            'user': item.user.username, 'info': reverse('crips_details', kwargs={'crip_id': item.id})
        } for i, item in enumerate(result['data'])]
        
        return JsonResponse(
            {
                'draw': result['draw'],
                'recordsTotal': result['recordsTotal'],
                'recordsFiltered': result['recordsFiltered'],
                'data': final_data,
                'grand_total': f"{format_number(grand_total)} TZS"
            }
        )
    users = CustomUser.objects.filter(is_active=True, deleted=False).order_by('username')
    return render(request, 'crips/crips.html', {'users': users})

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