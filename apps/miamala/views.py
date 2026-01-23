import logging
from typing import Dict, Any, List, Optional
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import QuerySet, Q, Sum, F
from django.db.models.functions import Lower
from decimal import Decimal

from .models import Selcompay, Lipanamba, Debts, Loans, Expenses, Mauzo
from apps.shops.models import Shop
from utils.util_functions import conv_timezone, format_number, selcom_profit, lipa_profit

# Configure logging
logger = logging.getLogger(__name__)

# --- DATABASE UTILITIES ---

def get_numeric_filter(field_name: str, search_value: str) -> Optional[Q]:
    """
    Translates filter_items() logic to Database Q objects for performance.
    Logic: '-100' (<=100), '100-' (>=100), '100' (==100)
    """
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

class BaseService:
    """Base class for common CRUD operations with performance optimizations"""
    @staticmethod
    def _get_shop(shop_id, user):
        if not shop_id: return user.shop
        return Shop.objects.get(id=shop_id)

# --- TRANSACTION SERVICES ---

class SelcomPayService(BaseService):
    @staticmethod
    def create_transaction(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            name = post_data.get('names', '').strip()
            amount = post_data.get('amount')
            if len(name) < 3: return {'success': False, 'sms': 'Names must have at least 3 characters.'}
            
            Selcompay.objects.create(
                name=name, amount=amount, profit=selcom_profit(amount),
                description=post_data.get('describe', '').strip() or None,
                user=user, shop=Shop.objects.get(id=post_data.get('shop'))
            )
            return {'success': True, 'sms': 'Transaction added successfully!'}
        except Exception as e:
            logger.error(f"SelcomPay Create Error: {e}")
            return {'success': False, 'sms': str(e)}

    @staticmethod
    def update_transaction(post_data: Dict[str, Any], trans_id: int, user) -> Dict[str, Any]:
        try:
            item = Selcompay.objects.get(id=trans_id)
            item.name = post_data.get('names', '').strip()
            item.amount = post_data.get('amount')
            item.profit = selcom_profit(post_data.get('amount'))
            item.description = post_data.get('describe', '').strip() or None
            item.shop = Shop.objects.get(id=post_data.get('shop'))
            item.save()
            return {'success': True, 'sms': 'Updated successfully!'}
        except Exception as e:
            return {'success': False, 'sms': str(e)}

    @staticmethod
    def delete_transaction(trans_id: int) -> Dict[str, Any]:
        Selcompay.objects.filter(id=trans_id).update(deleted=True)
        return {'success': True, 'sms': 'Transaction deleted successfully!'}

class LipaNambaService(BaseService):
    @staticmethod
    def create_transaction(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            Lipanamba.objects.create(
                name=post_data.get('names', '').strip(),
                amount=post_data.get('amount'), profit=lipa_profit(post_data.get('amount')),
                description=post_data.get('describe', '').strip() or None,
                user=user, shop=Shop.objects.get(id=post_data.get('shop'))
            )
            return {'success': True, 'sms': 'Transaction added successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed'}

    @staticmethod
    def update_transaction(post_data: Dict[str, Any], trans_id: int, user) -> Dict[str, Any]:
        try:
            obj = Lipanamba.objects.get(id=trans_id)
            obj.name = post_data.get('names', '').strip()
            obj.amount = post_data.get('amount')
            obj.profit = lipa_profit(post_data.get('amount'))
            obj.description = post_data.get('describe', '').strip() or None
            obj.shop = Shop.objects.get(id=post_data.get('shop'))
            obj.save()
            return {'success': True, 'sms': 'Transaction updated successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed'}

    @staticmethod
    def delete_transaction(trans_id: int) -> Dict[str, Any]:
        Lipanamba.objects.filter(id=trans_id).update(deleted=True)
        return {'success': True, 'sms': 'Transaction deleted successfully!'}

class DebtsService(BaseService):
    @staticmethod
    def create_debt(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            Debts.objects.create(
                name=post_data.get('names', '').strip(),
                amount=post_data.get('amount'),
                description=post_data.get('describe', '').strip() or None,
                user=user, shop=Shop.objects.get(id=post_data.get('shop'))
            )
            return {'success': True, 'sms': 'New debt added successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def update_debt(post_data: Dict[str, Any], debt_id: int, user) -> Dict[str, Any]:
        try:
            debt = Debts.objects.get(id=debt_id)
            paid_val = post_data.get('paid')
            if paid_val:
                val = Decimal(paid_val)
                if val < 0: debt.paid += abs(val)
                else: debt.amount += val
            debt.name = post_data.get('names', '').strip()
            debt.description = post_data.get('describe', '').strip() or None
            debt.shop = Shop.objects.get(id=post_data.get('shop'))
            debt.save()
            return {'success': True, 'sms': 'Debt updated successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def delete_debt(debt_id: int) -> Dict[str, Any]:
        Debts.objects.filter(id=debt_id).update(deleted=True)
        return {'success': True, 'sms': 'Debt deleted successfully!'}

class LoansService(BaseService):
    @staticmethod
    def create_loan(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            Loans.objects.create(
                name=post_data.get('names', '').strip(),
                amount=post_data.get('amount'),
                description=post_data.get('describe', '').strip() or None,
                user=user, shop=Shop.objects.get(id=post_data.get('shop'))
            )
            return {'success': True, 'sms': 'New loan added successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed'}

    @staticmethod
    def update_loan(post_data: Dict[str, Any], loan_id: int, user) -> Dict[str, Any]:
        try:
            loan = Loans.objects.get(id=loan_id)
            paid_val = post_data.get('paid')
            if paid_val:
                val = Decimal(paid_val)
                if val < 0: loan.paid += abs(val)
                else: loan.amount += val
            loan.name = post_data.get('names', '').strip()
            loan.description = post_data.get('describe', '').strip() or None
            loan.shop = Shop.objects.get(id=post_data.get('shop'))
            loan.save()
            return {'success': True, 'sms': 'Loan updated successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed'}

    @staticmethod
    def delete_loan(loan_id: int) -> Dict[str, Any]:
        Loans.objects.filter(id=loan_id).update(deleted=True)
        return {'success': True, 'sms': 'Loan deleted successfully!'}

class ExpensesService(BaseService):
    @staticmethod
    def create_expense(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            shop = Shop.objects.get(id=post_data.get('shop'))
            Expenses.objects.create(
                dates=post_data.get('dates'), title=post_data.get('title', '').strip(),
                amount=post_data.get('amount'), description=post_data.get('describe', '').strip() or None,
                user=user, shop=shop
            )
            return {'success': True, 'sms': 'Expense added successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def update_expense(post_data: Dict[str, Any], expense_id: int, user) -> Dict[str, Any]:
        try:
            expense = Expenses.objects.get(id=expense_id)
            expense.dates = post_data.get('dates')
            expense.title = post_data.get('title', '').strip()
            expense.amount = post_data.get('amount')
            expense.shop = Shop.objects.get(id=post_data.get('shop'))
            expense.description = post_data.get('describe', '').strip() or None
            expense.save()
            return {'success': True, 'sms': 'Expense updated successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def delete_expense(expense_id: int) -> Dict[str, Any]:
        Expenses.objects.filter(id=expense_id).update(deleted=True)
        return {'success': True, 'sms': 'Expense deleted successfully!'}

    @staticmethod
    def view_expense(expense_id: int) -> Dict[str, Any]:
        try:
            exp = Expenses.objects.select_related('user', 'shop').get(id=expense_id)
            return {
                'success': True,
                'regdate': conv_timezone(exp.created_at, '%d-%b-%Y %H:%M:%S'),
                'updatedate': conv_timezone(exp.updated_at, '%d-%b-%Y %H:%M:%S'),
                'dates': exp.dates.strftime('%d-%b-%Y'),
                'dates_form': exp.dates, 'title': exp.title,
                'amount': format_number(exp.amount) + ' TZS',
                'amount_form': exp.amount, 'describe': exp.description or 'N/A',
                'user': exp.user.username, 'shop': f"{exp.shop.names} ({exp.shop.abbrev})",
                'shop_id': exp.shop.id,
            }
        except Exception: return {'success': False, 'sms': 'Expense not found.'}

class MauzoService(BaseService):
    @staticmethod
    def create_mauzo(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        try:
            Mauzo.objects.create(
                dates=post_data.get('dates'), amount=post_data.get('amount'),
                description=post_data.get('describe', '').strip() or None,
                user=user, shop=Shop.objects.get(id=post_data.get('shop'))
            )
            return {'success': True, 'sms': 'Sales recorded successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def update_mauzo(post_data: Dict[str, Any], mauzo_id: int, user) -> Dict[str, Any]:
        try:
            item = Mauzo.objects.get(id=mauzo_id)
            item.dates = post_data.get('dates')
            item.amount = post_data.get('amount')
            item.shop = Shop.objects.get(id=post_data.get('shop'))
            item.description = post_data.get('describe', '').strip() or None
            item.save()
            return {'success': True, 'sms': 'Sales updated successfully!'}
        except Exception: return {'success': False, 'sms': 'Operation failed..!'}

    @staticmethod
    def delete_mauzo(mauzo_id: int) -> Dict[str, Any]:
        Mauzo.objects.filter(id=mauzo_id).update(deleted=True)
        return {'success': True, 'sms': 'Sales deleted successfully!'}

    @staticmethod
    def view_mauzo(mauzo_id: int) -> Dict[str, Any]:
        try:
            m = Mauzo.objects.select_related('user', 'shop').get(id=mauzo_id)
            return {
                'success': True,
                'regdate': conv_timezone(m.created_at, '%d-%b-%Y %H:%M:%S'),
                'updatedate': conv_timezone(m.updated_at, '%d-%b-%Y %H:%M:%S'),
                'dates': m.dates.strftime('%d-%b-%Y'),
                'dates_form': m.dates, 'amount': format_number(m.amount) + ' TZS',
                'amount_form': m.amount, 'describe': m.description or 'N/A',
                'user': m.user.username, 'shop': f"{m.shop.names} ({m.shop.abbrev})",
                'shop_id': m.shop.id,
            }
        except Exception: return {'success': False, 'sms': 'Sales not found.'}

# --- DATATABLES ENGINE (OPTIMIZED) ---

class DataTablesEngine:
    """Core engine to handle DB-level DataTables operations with correct record counting"""
    
    @staticmethod
    def handle_request(request: HttpRequest, queryset: QuerySet, 
                       search_fields: List[str], 
                       column_map: Dict[int, str],
                       numeric_fields: List[str] = None) -> Dict[str, Any]:
        
        # 1. Base Count (Unfiltered)
        records_total = queryset.count()
        
        # 2. Extract DataTables parameters
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_val = request.POST.get('search[value]', '').strip()
        
        # 3. Date Filtering (DB Level)
        start_date = request.POST.get('startdate')
        end_date = request.POST.get('enddate')
        date_field = 'dates' if 'dates' in [f.name for f in queryset.model._meta.fields] else 'created_at'
        
        if start_date:
            try: queryset = queryset.filter(**{f"{date_field}__gte": parse(start_date)})
            except: pass
        if end_date:
            try: queryset = queryset.filter(**{f"{date_field}__lte": parse(end_date)})
            except: pass

        # 4. Global Search (DB Level)
        if search_val:
            q_obj = Q()
            for field in search_fields:
                q_obj |= Q(**{f"{field}__icontains": search_val})
            queryset = queryset.filter(q_obj)

        # 5. Individual Column Search (Replacing filter_items loop)
        for i in range(len(column_map)):
            col_search = request.POST.get(f'columns[{i}][search][value]', '').strip()
            if col_search:
                field = column_map.get(i)
                if numeric_fields and field in numeric_fields:
                    num_q = get_numeric_filter(field, col_search)
                    if num_q: queryset = queryset.filter(num_q)
                else:
                    queryset = queryset.filter(**{f"{field}__icontains": col_search})

        # 6. Filtered Count (Before slicing)
        records_filtered = queryset.count()

        # 7. Sorting (DB Level)
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

        # 8. Pagination
        paged_data = queryset[start:start+length] if length > 0 else queryset
        
        return {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': paged_data,
            'full_queryset': queryset # For totals/aggregates
        }

# --- VIEW FUNCTIONS ---

@never_cache
@login_required
def selcompay (request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Selcompay.objects.filter(deleted=False).select_related('user', 'shop')
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'created_at', 2: 'name', 3: 'amount', 4: 'profit', 5: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['name', 'description'], cols, ['amount', 'profit'])
        
        # Grand Totals (DB level)
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'), t_prof=Sum('profit'))
        
        final_data = []
        for i, item in enumerate(dt['data']):
            final_data.append({
                'count': int(request.POST.get('start', 0)) + i + 1,
                'id': item.id,
                'dates': conv_timezone(item.created_at, '%d-%b-%Y %H:%M'),
                'names': item.name, 'shop': item.shop.abbrev,
                'user': item.user.username, 'amount': format_number(item.amount),
                'profit': format_number(item.profit), 'describe': item.description or "",
                'action': ""
            })

        return JsonResponse({
            'draw': dt['draw'],
            'recordsTotal': dt['recordsTotal'],
            'recordsFiltered': dt['recordsFiltered'],
            'data': final_data,
            'total_amount': format_number(totals['t_amt'] or 0),
            'total_profit': format_number(totals['t_prof'] or 0)
        })
    return render(request, 'miamala/selcom.html', {'shops': Shop.objects.all().order_by('names')})

@never_cache
@login_required
def lipanamba(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Lipanamba.objects.filter(deleted=False).select_related('user', 'shop')
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'created_at', 2: 'name', 3: 'amount', 4: 'profit', 5: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['name', 'description'], cols, ['amount', 'profit'])
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'), t_prof=Sum('profit'))
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'dates': conv_timezone(item.created_at, '%d-%b-%Y %H:%M'),
            'names': item.name, 'shop': item.shop.abbrev, 'user': item.user.username,
            'amount': format_number(item.amount), 'profit': format_number(item.profit),
            'describe': item.description or "", 'action': ""
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'],
            'recordsTotal': dt['recordsTotal'],
            'recordsFiltered': dt['recordsFiltered'],
            'data': final_data,
            'total_amount': format_number(totals['t_amt'] or 0),
            'total_profit': format_number(totals['t_prof'] or 0)
        })
    return render(request, 'miamala/lipanamba.html', {'shops': Shop.objects.all().order_by('names')})

@never_cache
@login_required
def debts(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Debts.objects.filter(deleted=False).select_related('user', 'shop').annotate(balance=F('amount')-F('paid'))
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'created_at', 2: 'name', 3: 'amount', 4: 'paid', 5: 'balance', 6: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['name', 'description'], cols, ['amount', 'paid', 'balance'])
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'), t_paid=Sum('paid'), t_bal=Sum(F('amount')-F('paid')))
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'dates': conv_timezone(item.created_at, '%d-%b-%Y %H:%M'),
            'names': item.name, 'amount': format_number(item.amount),
            'paid': format_number(item.paid), 'balance': format_number(item.amount - item.paid),
            'describe': item.description or "", 'shop': item.shop.abbrev, 'user': item.user.username, 'action': ""
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'],
            'recordsTotal': dt['recordsTotal'],
            'recordsFiltered': dt['recordsFiltered'],
            'data': final_data,
            'total_amount': format_number(totals['t_amt'] or 0),
            'total_paid': format_number(totals['t_paid'] or 0),
            'total_balance': format_number(totals['t_bal'] or 0)
        })
    return render(request, 'miamala/debts.html', {'shops': Shop.objects.all().order_by('names')})

@never_cache
@login_required
def loans(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Loans.objects.filter(deleted=False).select_related('user', 'shop').annotate(balance=F('amount')-F('paid'))
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'created_at', 2: 'name', 3: 'amount', 4: 'paid', 5: 'balance', 6: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['name', 'description'], cols, ['amount', 'paid', 'balance'])
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'), t_paid=Sum('paid'), t_bal=Sum(F('amount')-F('paid')))
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'dates': conv_timezone(item.created_at, '%d-%b-%Y %H:%M'),
            'names': item.name, 'amount': format_number(item.amount),
            'paid': format_number(item.paid), 'balance': format_number(item.amount - item.paid),
            'describe': item.description or "", 'shop': item.shop.abbrev, 'user': item.user.username, 'action': ""
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'],
            'recordsTotal': dt['recordsTotal'],
            'recordsFiltered': dt['recordsFiltered'],
            'data': final_data,
            'total_amount': format_number(totals['t_amt'] or 0),
            'total_paid': format_number(totals['t_paid'] or 0),
            'total_balance': format_number(totals['t_bal'] or 0)
        })
    return render(request, 'miamala/loans.html', {'shops': Shop.objects.all().order_by('names')})

@never_cache
@login_required
def expenses(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Expenses.objects.filter(deleted=False).select_related('user', 'shop')
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'dates', 2: 'title', 3: 'amount', 4: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['title', 'description'], cols, ['amount'])
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'))
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'dates': item.dates.strftime('%d-%b-%Y'),
            'title': item.title, 'amount': format_number(item.amount),
            'describe': item.description or "", 'shop': item.shop.abbrev,
            'user': item.user.username, 'action': ""
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'], 'recordsTotal': dt['recordsTotal'], 'data': final_data,
            'recordsFiltered': dt['recordsFiltered'], 'total_amount': format_number(totals['t_amt'] or 0)
        })
    return render(request, 'miamala/expenses.html', {'shops': Shop.objects.all().order_by('names')})

@never_cache
@login_required
def mauzo(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        qs = Mauzo.objects.filter(deleted=False).select_related('user', 'shop')
        if not request.user.is_admin:
            qs = qs.filter(shop=request.user.shop)
        cols = {1: 'dates', 2: 'amount', 3: 'shop__abbrev'}
        
        dt = DataTablesEngine.handle_request(request, qs, ['description'], cols, ['amount'])
        totals = dt['full_queryset'].aggregate(t_amt=Sum('amount'))
        
        final_data = [{
            'count': int(request.POST.get('start', 0)) + i + 1,
            'id': item.id, 'dates': item.dates.strftime('%d-%b-%Y'),
            'amount': format_number(item.amount), 'describe': item.description or "",
            'shop': item.shop.abbrev, 'user': item.user.username, 'action': ""
        } for i, item in enumerate(dt['data'])]

        return JsonResponse({
            'draw': dt['draw'], 'recordsTotal': dt['recordsTotal'], 'data': final_data,
            'recordsFiltered': dt['recordsFiltered'], 'total_amount': format_number(totals['t_amt'] or 0)
        })
    return render(request, 'miamala/mauzo.html', {'shops': Shop.objects.all().order_by('names')})

# --- ACTION ROUTERS ---

@never_cache
@login_required
def selcompay_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        t_edit, t_del = post.get('selcom_edit'), post.get('selcom_delete')
        if t_del: return JsonResponse(SelcomPayService.delete_transaction(t_del))
        if t_edit: return JsonResponse(SelcomPayService.update_transaction(post, t_edit, request.user))
        return JsonResponse(SelcomPayService.create_transaction(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})

@never_cache
@login_required
def lipanamba_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        t_edit, t_del = post.get('lipa_edit'), post.get('lipa_delete')
        if t_del: return JsonResponse(LipaNambaService.delete_transaction(t_del))
        if t_edit: return JsonResponse(LipaNambaService.update_transaction(post, t_edit, request.user))
        return JsonResponse(LipaNambaService.create_transaction(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})

@never_cache
@login_required
def debts_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        d_edit, d_del = post.get('debt_edit'), post.get('debt_delete')
        if d_del: return JsonResponse(DebtsService.delete_debt(d_del))
        if d_edit: return JsonResponse(DebtsService.update_debt(post, d_edit, request.user))
        return JsonResponse(DebtsService.create_debt(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})

@never_cache
@login_required
def loans_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        l_edit, l_del = post.get('loan_edit'), post.get('loan_delete')
        if l_del: return JsonResponse(LoansService.delete_loan(l_del))
        if l_edit: return JsonResponse(LoansService.update_loan(post, l_edit, request.user))
        return JsonResponse(LoansService.create_loan(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})

@never_cache
@login_required
def expenses_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        e_edit, e_del, e_view = post.get('expense_edit'), post.get('expense_delete'), post.get('expense_view')
        if e_view: return JsonResponse(ExpensesService.view_expense(e_view))
        if e_del: return JsonResponse(ExpensesService.delete_expense(e_del))
        if e_edit: return JsonResponse(ExpensesService.update_expense(post, e_edit, request.user))
        return JsonResponse(ExpensesService.create_expense(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})

@never_cache
@login_required
def mauzo_actions(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        post = request.POST
        m_edit, m_del, m_view = post.get('mauzo_edit'), post.get('mauzo_delete'), post.get('mauzo_view')
        if m_view: return JsonResponse(MauzoService.view_mauzo(m_view))
        if m_del: return JsonResponse(MauzoService.delete_mauzo(m_del))
        if m_edit: return JsonResponse(MauzoService.update_mauzo(post, m_edit, request.user))
        return JsonResponse(MauzoService.create_mauzo(post, request.user))
    return JsonResponse({'success': False, 'sms': 'Invalid request'})
