import logging
import zoneinfo
from typing import Dict, Any, List
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import QuerySet, Q
from decimal import Decimal

from datetime import datetime

from .models import Selcompay, Lipanamba, Debts, Loans, Expenses
from utils.util_functions import admin_required, conv_timezone, filter_items, format_number, selcom_profit, lipa_profit

# Configure logging
logger = logging.getLogger(__name__)


# SELCOMPAY MANAGEMENT SERVICES
class SelcomPayService:
    """Service class for handling SelcomPay management operations"""
    
    @staticmethod
    def create_transaction(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SelcomPay transaction"""
        try:
            trans_names = post_data.get('names', '').strip()
            trans_amount = post_data.get('amount')
            trans_describe = post_data.get('describe', '').strip()
            
            if len(trans_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            trans_describe = None if trans_describe == "" else trans_describe
            
            Selcompay.objects.create(
                name=trans_names,
                amount=trans_amount,
                description=trans_describe
            )
            
            logger.info("New SelcomPay transaction created successfully")
            return {'success': True, 'sms': 'Transaction added successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating SelcomPay transaction: {str(e)}")
            return {'success': False, 'sms': str(e)}
    
    @staticmethod
    def update_transaction(post_data: Dict[str, Any], trans_id: int) -> Dict[str, Any]:
        """Update an existing SelcomPay transaction"""
        try:
            transaction = Selcompay.objects.get(id=trans_id)
            trans_names = post_data.get('names', '').strip()
            trans_amount = post_data.get('amount')
            trans_describe = post_data.get('describe', '').strip()
            
            if len(trans_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            trans_describe = None if trans_describe == "" else trans_describe
            
            if transaction.name != trans_names:
                transaction.name = trans_names
            if transaction.amount != trans_amount:
                transaction.amount = trans_amount
            if transaction.description != trans_describe:
                transaction.description = trans_describe
                
            transaction.save()
            
            logger.info(f"SelcomPay transaction {trans_id} updated successfully")
            return {'success': True, 'sms': 'Transaction updated successfully!'}
            
        except Selcompay.DoesNotExist:
            return {'success': False, 'sms': 'Transaction not found.'}
        except Exception as e:
            logger.error(f"Error updating SelcomPay transaction {trans_id}: {str(e)}")
            return {'success': False, 'sms': str(e)}
    
    @staticmethod
    def delete_transaction(trans_id: int) -> Dict[str, Any]:
        """Delete a SelcomPay transaction"""
        try:
            transaction = Selcompay.objects.get(id=trans_id)
            transaction.deleted = 1
            transaction.save()
            
            logger.info(f"SelcomPay transaction {trans_id} deleted successfully")
            return {'success': True, 'sms': 'Transaction deleted successfully!'}
            
        except Selcompay.DoesNotExist:
            return {'success': False, 'sms': 'Transaction not found.'}
        except Exception as e:
            logger.error(f"Error deleting SelcomPay transaction {trans_id}: {str(e)}")
            return {'success': False, 'sms': str(e)}


# LIPANAMBA MANAGEMENT SERVICES
class LipaNambaService:
    """Service class for handling LipaNamba management operations"""
    
    @staticmethod
    def create_transaction(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new LipaNamba transaction"""
        try:
            trans_names = post_data.get('names', '').strip()
            trans_amount = post_data.get('amount')
            trans_describe = post_data.get('describe', '').strip()
            
            if len(trans_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            trans_describe = None if trans_describe == "" else trans_describe
            
            Lipanamba.objects.create(
                name=trans_names,
                amount=trans_amount,
                description=trans_describe
            )
            
            logger.info("New LipaNamba transaction created successfully")
            return {'success': True, 'sms': 'Transaction added successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating LipaNamba transaction: {str(e)}")
            return {'success': False, 'sms': 'Operation failed'}
    
    @staticmethod
    def update_transaction(post_data: Dict[str, Any], trans_id: int) -> Dict[str, Any]:
        """Update an existing LipaNamba transaction"""
        try:
            transaction = Lipanamba.objects.get(id=trans_id)
            trans_names = post_data.get('names', '').strip()
            trans_amount = post_data.get('amount')
            trans_describe = post_data.get('describe', '').strip()
            
            if len(trans_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            trans_describe = None if trans_describe == "" else trans_describe
            
            if transaction.name != trans_names:
                transaction.name = trans_names
            if transaction.amount != trans_amount:
                transaction.amount = trans_amount
            if transaction.description != trans_describe:
                transaction.description = trans_describe
                
            transaction.save()
            
            logger.info(f"LipaNamba transaction {trans_id} updated successfully")
            return {'success': True, 'sms': 'Transaction updated successfully!'}
            
        except Lipanamba.DoesNotExist:
            return {'success': False, 'sms': 'Transaction not found.'}
        except Exception as e:
            logger.error(f"Error updating LipaNamba transaction {trans_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed'}
    
    @staticmethod
    def delete_transaction(trans_id: int) -> Dict[str, Any]:
        """Delete a LipaNamba transaction"""
        try:
            transaction = Lipanamba.objects.get(id=trans_id)
            transaction.deleted = 1
            transaction.save()
            
            logger.info(f"LipaNamba transaction {trans_id} deleted successfully")
            return {'success': True, 'sms': 'Transaction deleted successfully!'}
            
        except Lipanamba.DoesNotExist:
            return {'success': False, 'sms': 'Transaction not found.'}
        except Exception as e:
            logger.error(f"Error deleting LipaNamba transaction {trans_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed'}


# DEBTS MANAGEMENT SERVICES
class DebtsService:
    """Service class for handling Debts management operations"""
    
    @staticmethod
    def create_debt(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new debt"""
        try:
            debt_names = post_data.get('names', '').strip()
            debt_amount = post_data.get('amount')
            debt_describe = post_data.get('describe', '').strip()
            
            if len(debt_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            debt_describe = None if debt_describe == "" else debt_describe
            
            Debts.objects.create(
                name=debt_names,
                amount=debt_amount,
                description=debt_describe
            )
            
            logger.info("New debt created successfully")
            return {'success': True, 'sms': 'New debt added successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating debt: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}
    
    @staticmethod
    def update_debt(post_data: Dict[str, Any], debt_id: int) -> Dict[str, Any]:
        """Update an existing debt"""
        try:
            debt = Debts.objects.get(id=debt_id)
            debt_names = post_data.get('names', '').strip()
            debt_paid = post_data.get('paid')
            debt_describe = post_data.get('describe', '').strip()
            
            if len(debt_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            if debt_paid:
                debt_paid = Decimal(debt_paid)
                if debt_paid < 0.0:
                    debt.paid = debt.paid + abs(debt_paid)
                else:
                    debt.amount = debt.amount + debt_paid
            
            debt_describe = None if debt_describe == "" else debt_describe
            
            if debt.name != debt_names:
                debt.name = debt_names
            if debt.description != debt_describe:
                debt.description = debt_describe
                
            debt.save()
            
            logger.info(f"Debt {debt_id} updated successfully")
            return {'success': True, 'sms': 'Debt details updated successfully!'}
            
        except Debts.DoesNotExist:
            return {'success': False, 'sms': 'Debt not found.'}
        except Exception as e:
            logger.error(f"Error updating debt {debt_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}
    
    @staticmethod
    def delete_debt(debt_id: int) -> Dict[str, Any]:
        """Delete a debt"""
        try:
            debt = Debts.objects.get(id=debt_id)
            debt.deleted = 1
            debt.save()
            
            logger.info(f"Debt {debt_id} deleted successfully")
            return {'success': True, 'sms': 'Debt deleted successfully!'}
            
        except Debts.DoesNotExist:
            return {'success': False, 'sms': 'Debt not found.'}
        except Exception as e:
            logger.error(f"Error deleting debt {debt_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}


# LOANS MANAGEMENT SERVICES
class LoansService:
    """Service class for handling Loans management operations"""
    
    @staticmethod
    def create_loan(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new loan"""
        try:
            loan_names = post_data.get('names', '').strip()
            loan_amount = post_data.get('amount')
            loan_describe = post_data.get('describe', '').strip()
            
            if len(loan_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            loan_describe = None if loan_describe == "" else loan_describe
            
            Loans.objects.create(
                name=loan_names,
                amount=loan_amount,
                description=loan_describe
            )
            
            logger.info("New loan created successfully")
            return {'success': True, 'sms': 'New loan added successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating loan: {str(e)}")
            return {'success': False, 'sms': str(e)}
    
    @staticmethod
    def update_loan(post_data: Dict[str, Any], loan_id: int) -> Dict[str, Any]:
        """Update an existing loan"""
        try:
            loan = Loans.objects.get(id=loan_id)
            loan_names = post_data.get('names', '').strip()
            loan_paid = post_data.get('paid')
            loan_describe = post_data.get('describe', '').strip()
            
            if len(loan_names) < 3:
                return {'success': False, 'sms': 'Names must have atleast 3 characters.'}
            
            if loan_paid:
                loan_paid = Decimal(loan_paid)
                if loan_paid < 0.0:
                    loan.paid = loan.paid + abs(loan_paid)
                else:
                    loan.amount = loan.amount + loan_paid
            
            loan_describe = None if loan_describe == "" else loan_describe
            
            if loan.name != loan_names:
                loan.name = loan_names
            if loan.description != loan_describe:
                loan.description = loan_describe
                
            loan.save()
            
            logger.info(f"Loan {loan_id} updated successfully")
            return {'success': True, 'sms': 'Loan details updated successfully!'}
            
        except Loans.DoesNotExist:
            return {'success': False, 'sms': 'Loan not found.'}
        except Exception as e:
            logger.error(f"Error updating loan {loan_id}: {str(e)}")
            return {'success': False, 'sms': str(e)}
    
    @staticmethod
    def delete_loan(loan_id: int) -> Dict[str, Any]:
        """Delete a loan"""
        try:
            loan = Loans.objects.get(id=loan_id)
            loan.deleted = 1
            loan.save()
            
            logger.info(f"Loan {loan_id} deleted successfully")
            return {'success': True, 'sms': 'Loan deleted successfully!'}
            
        except Loans.DoesNotExist:
            return {'success': False, 'sms': 'Loan not found.'}
        except Exception as e:
            logger.error(f"Error deleting loan {loan_id}: {str(e)}")
            return {'success': False, 'sms': str(e)}


# EXPENSES MANAGEMENT SERVICES
class ExpensesService:
    """Service class for handling Expenses management operations"""
    
    @staticmethod
    def create_expense(post_data: Dict[str, Any], user) -> Dict[str, Any]:
        """Create a new expense"""
        try:
            exp_date = post_data.get('dates')
            exp_title = post_data.get('title', '').strip()
            exp_amount = post_data.get('amount')
            exp_describe = post_data.get('describe', '').strip()
            
            if len(exp_title) < 3:
                return {'success': False, 'sms': 'Title must have atleast 3 characters.'}
            
            exp_describe = None if exp_describe == "" else exp_describe
            
            Expenses.objects.create(
                dates=exp_date,
                title=exp_title,
                amount=exp_amount,
                description=exp_describe,
                user=user,
                shop=user.shop
            )
            
            logger.info("New expense created successfully")
            return {'success': True, 'sms': 'New expense added successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}
    
    @staticmethod
    def update_expense(post_data: Dict[str, Any], expense_id: int, user) -> Dict[str, Any]:
        """Update an existing expense"""
        try:
            expense = Expenses.objects.get(id=expense_id)
            exp_date = post_data.get('dates')
            exp_title = post_data.get('title', '').strip()
            exp_amount = post_data.get('amount')
            exp_describe = post_data.get('describe', '').strip()
            
            if len(exp_title) < 3:
                return {'success': False, 'sms': 'Title must have atleast 3 characters.'}
            
            exp_describe = None if exp_describe == "" else exp_describe
            
            expense.dates = exp_date
            expense.title = exp_title
            expense.amount = exp_amount
            expense.description = exp_describe
            expense.user = user
            expense.shop = user.shop
            expense.save()
            
            logger.info(f"Expense {expense_id} updated successfully")
            return {'success': True, 'sms': 'Expense details updated successfully!'}
            
        except Expenses.DoesNotExist:
            return {'success': False, 'sms': 'Expense not found.'}
        except Exception as e:
            logger.error(f"Error updating expense {expense_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}
    
    @staticmethod
    def delete_expense(expense_id: int) -> Dict[str, Any]:
        """Delete an expense"""
        try:
            expense = Expenses.objects.get(id=expense_id)
            expense.deleted = 1
            expense.save()
            
            logger.info(f"Expense {expense_id} deleted successfully")
            return {'success': True, 'sms': 'Expense deleted successfully!'}
            
        except Expenses.DoesNotExist:
            return {'success': False, 'sms': 'Expense not found.'}
        except Exception as e:
            logger.error(f"Error deleting expense {expense_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}
    
    @staticmethod
    def view_expense(expense_id: int) -> Dict[str, Any]:
        """View expense details"""
        try:
            expense = Expenses.objects.get(id=expense_id)
            
            return {
                'success': True,
                'regdate': expense.created_at.strftime('%d-%b-%Y %H:%M:%S'),
                'dates': expense.dates.strftime('%d-%b-%Y'),
                'dates_form': expense.dates,
                'title': expense.title,
                'amount': format_number(expense.amount) + ' TZS',
                'amount_form': expense.amount,
                'describe': 'N/A' if expense.description is None else expense.description,
                'user': expense.user.username,
                'shop': f"{expense.shop.names} ({expense.shop.abbrev})",
            }
            
        except Expenses.DoesNotExist:
            return {'success': False, 'sms': 'Expense not found.'}
        except Exception as e:
            logger.error(f"Error viewing expense {expense_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed..!'}


# DATATABLES UTILITIES
class DataTablesService:
    """Service class for handling DataTables functionality"""
    
    @staticmethod
    def parse_request_params(request: HttpRequest) -> Dict[str, Any]:
        """Parse DataTables AJAX request parameters"""
        return {
            'draw': int(request.POST.get('draw', 0)),
            'start': int(request.POST.get('start', 0)),
            'length': int(request.POST.get('length', 10)),
            'search_value': request.POST.get('search[value]', ''),
            'order_column_index': int(request.POST.get('order[0][column]', 1)),
            'order_dir': request.POST.get('order[0][dir]', 'desc'),
            'start_date_str': request.POST.get('startdate'),
            'end_date_str': request.POST.get('enddate'),
        }
    
    @staticmethod
    def apply_date_filtering(queryset: QuerySet, start_date_str: str, end_date_str: str) -> QuerySet:
        """Apply date range filtering to queryset"""
        try:
            parsed_start_date = None
            parsed_end_date = None
            
            if start_date_str:
                parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
            
            if end_date_str:
                parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
            
            if parsed_start_date and parsed_end_date:
                return queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
            elif parsed_start_date:
                return queryset.filter(created_at__gte=parsed_start_date)
            elif parsed_end_date:
                return queryset.filter(created_at__lte=parsed_end_date)
                
        except Exception as e:
            logger.warning(f"Date filtering error: {str(e)}")
        
        return queryset
    
    @staticmethod
    def apply_sorting(data: List[Dict], column_mapping: Dict, order_column_index: int, order_dir: str) -> List[Dict]:
        """Apply sorting to data list"""
        order_column_name = column_mapping.get(order_column_index, 'dates')
        reverse_order = order_dir == 'desc'
        
        return sorted(data, key=lambda x: x[order_column_name], reverse=reverse_order)
    
    @staticmethod
    def apply_column_filtering(data: List[Dict], request: HttpRequest, column_mapping: Dict, column_filter_types: Dict) -> List[Dict]:
        """Apply individual column filtering"""
        filtered_data = data
        
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    filtered_data = [
                        item for item in filtered_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]
        
        return filtered_data
    
    @staticmethod
    def apply_global_search(data: List[Dict], search_value: str) -> List[Dict]:
        """Apply global search filtering"""
        if not search_value:
            return data
        
        search_lower = search_value.lower()
        return [
            item for item in data 
            if any(str(value).lower().find(search_lower) != -1 for value in item.values())
        ]
    
    @staticmethod
    def paginate_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """Apply pagination to data"""
        if length < 0:
            return data
        return data[start:start + length]
    
    @staticmethod
    def calculate_row_count_start(start: int, length: int) -> int:
        """Calculate row count start for pagination"""
        page_number = start // length + 1 if length > 0 else 1
        return (page_number - 1) * length + 1


# SELCOMPAY DATA PROCESSING
class SelcomPayDataService:
    """Service class for SelcomPay data processing"""
    
    COLUMN_MAPPING = {
        0: 'id',
        1: 'dates',
        2: 'names',
        3: 'amount',
        4: 'profit',
    }
    
    COLUMN_FILTER_TYPES = {
        'profit': 'numeric',
        'amount': 'numeric',
    }
    
    @staticmethod
    def prepare_base_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """Convert SelcomPay queryset to list of dicts"""
        return [
            {
                'id': transact.id,
                'dates': transact.created_at,
                'names': transact.name,
                'amount': transact.amount,
                'profit': selcom_profit(transact.amount),
                'describe': transact.description if transact.description else ""
            }
            for transact in queryset
        ]
    
    @staticmethod
    def format_final_data(data: List[Dict], row_count_start: int) -> List[Dict]:
        """Format data for final DataTables response"""
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'profit': format_number(item.get('profit')),
                'describe': item.get('describe'),
                'action': ""
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_totals(data: List[Dict]) -> Dict[str, str]:
        """Calculate grand totals for SelcomPay data"""
        total_amount = sum(item['amount'] for item in data)
        total_profit = sum(item['profit'] for item in data)
        return {
            'total_amount': format_number(total_amount),
            'total_profit': format_number(total_profit),
        }


# LIPANAMBA DATA PROCESSING
class LipaNambaDataService:
    """Service class for LipaNamba data processing"""
    
    COLUMN_MAPPING = {
        0: 'id',
        1: 'dates',
        2: 'names',
        3: 'amount',
        4: 'profit',
        5: 'describe'
    }
    
    COLUMN_FILTER_TYPES = {
        'profit': 'numeric',
        'amount': 'numeric',
    }
    
    @staticmethod
    def prepare_base_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """Convert LipaNamba queryset to list of dicts"""
        return [
            {
                'id': transact.id,
                'dates': transact.created_at,
                'names': transact.name,
                'amount': transact.amount,
                'profit': lipa_profit(transact.amount),
                'describe': transact.description if transact.description else ""
            }
            for transact in queryset
        ]
    
    @staticmethod
    def format_final_data(data: List[Dict], row_count_start: int) -> List[Dict]:
        """Format data for final DataTables response"""
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'profit': format_number(item.get('profit')),
                'describe': item.get('describe'),
                'action': ""
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_totals(data: List[Dict]) -> Dict[str, str]:
        """Calculate grand totals for LipaNamba data"""
        total_amount = sum(item['amount'] for item in data)
        total_profit = sum(item['profit'] for item in data)
        return {
            'total_amount': format_number(total_amount),
            'total_profit': format_number(total_profit),
        }


# DEBTS DATA PROCESSING
class DebtsDataService:
    """Service class for Debts data processing"""
    
    COLUMN_MAPPING = {
        0: 'id',
        1: 'dates',
        2: 'names',
        3: 'amount',
        4: 'paid',
        5: 'balance',
        6: 'describe'
    }
    
    COLUMN_FILTER_TYPES = {
        'paid': 'numeric',
        'amount': 'numeric',
        'balance': 'numeric',
    }
    
    @staticmethod
    def prepare_base_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """Convert Debts queryset to list of dicts"""
        return [
            {
                'id': debt.id,
                'dates': debt.created_at,
                'names': debt.name,
                'amount': debt.amount,
                'paid': debt.paid,
                'balance': debt.amount - debt.paid,
                'describe': debt.description if debt.description else ""
            }
            for debt in queryset
        ]
    
    @staticmethod
    def format_final_data(data: List[Dict], row_count_start: int) -> List[Dict]:
        """Format data for final DataTables response"""
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'paid': format_number(item.get('paid')),
                'balance': format_number(item.get('balance')),
                'describe': item.get('describe'),
                'action': ""
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_totals(data: List[Dict]) -> Dict[str, str]:
        """Calculate grand totals for Debts data"""
        total_amount = sum(item['amount'] for item in data)
        total_paid = sum(item['paid'] for item in data)
        total_balance = sum(item['balance'] for item in data)
        return {
            'total_amount': format_number(total_amount),
            'total_paid': format_number(total_paid),
            'total_balance': format_number(total_balance),
        }


# LOANS DATA PROCESSING
class LoansDataService:
    """Service class for Loans data processing"""
    
    COLUMN_MAPPING = {
        0: 'id',
        1: 'dates',
        2: 'names',
        3: 'amount',
        4: 'paid',
        5: 'balance',
        6: 'describe'
    }
    
    COLUMN_FILTER_TYPES = {
        'paid': 'numeric',
        'amount': 'numeric',
        'balance': 'numeric',
    }
    
    @staticmethod
    def prepare_base_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """Convert Loans queryset to list of dicts"""
        return [
            {
                'id': loan.id,
                'dates': loan.created_at,
                'names': loan.name,
                'amount': loan.amount,
                'paid': loan.paid,
                'balance': loan.amount - loan.paid,
                'describe': loan.description if loan.description else ""
            }
            for loan in queryset
        ]
    
    @staticmethod
    def format_final_data(data: List[Dict], row_count_start: int) -> List[Dict]:
        """Format data for final DataTables response"""
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'paid': format_number(item.get('paid')),
                'balance': format_number(item.get('balance')),
                'describe': item.get('describe'),
                'action': ""
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_totals(data: List[Dict]) -> Dict[str, str]:
        """Calculate grand totals for Loans data"""
        total_amount = sum(item['amount'] for item in data)
        total_paid = sum(item['paid'] for item in data)
        total_balance = sum(item['balance'] for item in data)
        return {
            'total_amount': format_number(total_amount),
            'total_paid': format_number(total_paid),
            'total_balance': format_number(total_balance),
        }


# EXPENSES DATA PROCESSING
class ExpensesDataService:
    """Service class for Expenses data processing"""
    
    COLUMN_MAPPING = {
        0: 'id',
        1: 'dates',
        2: 'title',
        3: 'amount',
        4: 'user',
        5: 'shop'
    }
    
    COLUMN_FILTER_TYPES = {
        'amount': 'numeric',
    }
    
    @staticmethod
    def prepare_base_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """Convert Expenses queryset to list of dicts"""
        return [
            {
                'id': expense.id,
                'dates': expense.dates,
                'title': expense.title,
                'amount': expense.amount,
                'user': expense.user.username,
                'shop': expense.shop.abbrev
            }
            for expense in queryset
        ]
    
    @staticmethod
    def format_final_data(data: List[Dict], row_count_start: int) -> List[Dict]:
        """Format data for final DataTables response"""
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': item.get('dates').strftime('%d-%b-%Y'),
                'title': item.get('title'),
                'amount': format_number(item.get('amount')),
                'user': item.get('user'),
                'shop': item.get('shop'),
                'action': ""
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_totals(data: List[Dict]) -> Dict[str, str]:
        """Calculate grand totals for Expenses data"""
        total_amount = sum(item['amount'] for item in data)
        return {
            'total_amount': format_number(total_amount),
        }
    
    @staticmethod
    def apply_date_filtering_legacy(queryset: QuerySet, start_date_str: str, end_date_str: str) -> QuerySet:
        """Apply date range filtering using legacy date format"""
        try:
            format_date_string = "%Y-%m-%d"
            date_range_filters = Q()
            
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.strptime(start_date_str, format_date_string).date()
            if end_date_str:
                end_date = datetime.strptime(end_date_str, format_date_string).date()

            if start_date and end_date:
                date_range_filters |= Q(dates__range=(start_date, end_date))
            else:
                if start_date:
                    date_range_filters |= Q(dates__gte=start_date)
                elif end_date:
                    date_range_filters |= Q(dates__lte=end_date)

            if date_range_filters:
                return queryset.filter(date_range_filters)
                
        except Exception as e:
            logger.warning(f"Date filtering error: {str(e)}")
        
        return queryset


# =============================================
# VIEW FUNCTIONS
# =============================================

@never_cache
@login_required
@admin_required()
def selcom_transactions_page(request: HttpRequest) -> HttpResponse:
    """Handle SelcomPay transactions page display and DataTables AJAX requests"""
    if request.method == "POST":
        try:
            # Parse request parameters
            params = DataTablesService.parse_request_params(request)
            
            # Base queryset
            queryset = Selcompay.objects.filter(deleted=False)
            
            # Apply date filtering
            queryset = DataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = SelcomPayDataService.prepare_base_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, SelcomPayDataService.COLUMN_MAPPING, 
                params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(
                base_data, request, SelcomPayDataService.COLUMN_MAPPING, 
                SelcomPayDataService.COLUMN_FILTER_TYPES
            )
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand totals
            records_filtered = len(base_data)
            grand_totals = SelcomPayDataService.calculate_grand_totals(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Calculate row count start
            row_count_start = DataTablesService.calculate_row_count_start(
                params['start'], params['length']
            )
            
            # Format final data
            final_data = SelcomPayDataService.format_final_data(paginated_data, row_count_start)
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_totals': grand_totals
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in selcom_transactions_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'miamala/selcom.html')


@never_cache
@login_required
@admin_required()
def selcom_transactions_actions(request: HttpRequest) -> JsonResponse:
    """Handle SelcomPay transaction actions (add, update, delete)"""
    if request.method == 'POST':
        try:
            post_data = request.POST
            trans_id = post_data.get('transact_id')
            delete_id = post_data.get('delete_id')
            
            # Route to appropriate service method
            if delete_id:
                result = SelcomPayService.delete_transaction(delete_id)
            elif trans_id:
                result = SelcomPayService.update_transaction(post_data, trans_id)
            else:
                result = SelcomPayService.create_transaction(post_data)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in selcom_transactions_actions: {str(e)}")
            return JsonResponse({'success': False, 'sms': str(e)})


@never_cache
@login_required
@admin_required()
def lipa_transactions_page(request: HttpRequest) -> HttpResponse:
    """Handle LipaNamba transactions page display and DataTables AJAX requests"""
    if request.method == "POST":
        try:
            # Parse request parameters
            params = DataTablesService.parse_request_params(request)
            
            # Base queryset
            queryset = Lipanamba.objects.filter(deleted=False)
            
            # Apply date filtering
            queryset = DataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = LipaNambaDataService.prepare_base_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, LipaNambaDataService.COLUMN_MAPPING, 
                params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(
                base_data, request, LipaNambaDataService.COLUMN_MAPPING, 
                LipaNambaDataService.COLUMN_FILTER_TYPES
            )
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand totals
            records_filtered = len(base_data)
            grand_totals = LipaNambaDataService.calculate_grand_totals(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Calculate row count start
            row_count_start = DataTablesService.calculate_row_count_start(
                params['start'], params['length']
            )
            
            # Format final data
            final_data = LipaNambaDataService.format_final_data(paginated_data, row_count_start)
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_totals': grand_totals
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in lipa_transactions_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'miamala/lipanamba.html')


@never_cache
@login_required
@admin_required()
def lipanamba_transactions_actions(request: HttpRequest) -> JsonResponse:
    """Handle LipaNamba transaction actions (add, update, delete)"""
    if request.method == 'POST':
        try:
            post_data = request.POST
            trans_id = post_data.get('transact_id')
            delete_id = post_data.get('delete_id')
            
            # Route to appropriate service method
            if delete_id:
                result = LipaNambaService.delete_transaction(delete_id)
            elif trans_id:
                result = LipaNambaService.update_transaction(post_data, trans_id)
            else:
                result = LipaNambaService.create_transaction(post_data)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in lipanamba_transactions_actions: {str(e)}")
            return JsonResponse({'success': False, 'sms': 'Operation failed'})


@never_cache
@login_required
@admin_required()
def debts_page(request: HttpRequest) -> HttpResponse:
    """Handle Debts page display and DataTables AJAX requests"""
    if request.method == "POST":
        try:
            # Parse request parameters
            params = DataTablesService.parse_request_params(request)
            
            # Base queryset
            queryset = Debts.objects.filter(deleted=False)
            
            # Apply date filtering
            queryset = DataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = DebtsDataService.prepare_base_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, DebtsDataService.COLUMN_MAPPING, 
                params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(
                base_data, request, DebtsDataService.COLUMN_MAPPING, 
                DebtsDataService.COLUMN_FILTER_TYPES
            )
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand totals
            records_filtered = len(base_data)
            grand_totals = DebtsDataService.calculate_grand_totals(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Calculate row count start
            row_count_start = DataTablesService.calculate_row_count_start(
                params['start'], params['length']
            )
            
            # Format final data
            final_data = DebtsDataService.format_final_data(paginated_data, row_count_start)
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_totals': grand_totals
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in debts_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'miamala/debts.html')


@never_cache
@login_required
@admin_required()
def debts_actions(request: HttpRequest) -> JsonResponse:
    """Handle Debts actions (add, update, delete)"""
    if request.method == 'POST':
        try:
            post_data = request.POST
            debt_id = post_data.get('debt_id')
            delete_id = post_data.get('delete_id')
            
            # Route to appropriate service method
            if delete_id:
                result = DebtsService.delete_debt(delete_id)
            elif debt_id:
                result = DebtsService.update_debt(post_data, debt_id)
            else:
                result = DebtsService.create_debt(post_data)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in debts_actions: {str(e)}")
            return JsonResponse({'success': False, 'sms': 'Operation failed..!'})


@never_cache
@login_required
@admin_required()
def loans_page(request: HttpRequest) -> HttpResponse:
    """Handle Loans page display and DataTables AJAX requests"""
    if request.method == "POST":
        try:
            # Parse request parameters
            params = DataTablesService.parse_request_params(request)
            
            # Base queryset
            queryset = Loans.objects.filter(deleted=False)
            
            # Apply date filtering
            queryset = DataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = LoansDataService.prepare_base_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, LoansDataService.COLUMN_MAPPING, 
                params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(
                base_data, request, LoansDataService.COLUMN_MAPPING, 
                LoansDataService.COLUMN_FILTER_TYPES
            )
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand totals
            records_filtered = len(base_data)
            grand_totals = LoansDataService.calculate_grand_totals(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Calculate row count start
            row_count_start = DataTablesService.calculate_row_count_start(
                params['start'], params['length']
            )
            
            # Format final data
            final_data = LoansDataService.format_final_data(paginated_data, row_count_start)
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_totals': grand_totals
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in loans_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'miamala/loans.html')


@never_cache
@login_required
@admin_required()
def loans_actions(request: HttpRequest) -> JsonResponse:
    """Handle Loans actions (add, update, delete)"""
    if request.method == 'POST':
        try:
            post_data = request.POST
            loan_id = post_data.get('loan_id')
            delete_id = post_data.get('delete_id')
            
            # Route to appropriate service method
            if delete_id:
                result = LoansService.delete_loan(delete_id)
            elif loan_id:
                result = LoansService.update_loan(post_data, loan_id)
            else:
                result = LoansService.create_loan(post_data)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in loans_actions: {str(e)}")
            return JsonResponse({'success': False, 'sms': str(e)})
        

@never_cache
@login_required
def expenses_page(request: HttpRequest) -> HttpResponse:
    """Handle Expenses page display and DataTables AJAX requests"""
    if request.method == "POST":
        try:
            # Parse request parameters
            params = DataTablesService.parse_request_params(request)
            
            # Base queryset with user restrictions
            queryset = Expenses.objects.filter(deleted=False)
            if not request.user.is_admin:
                queryset = queryset.filter(shop=request.user.shop)
            
            # Apply date filtering (using legacy method for expenses)
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            queryset = ExpensesDataService.apply_date_filtering_legacy(
                queryset, start_date, end_date
            )
            
            # Prepare base data
            base_data = ExpensesDataService.prepare_base_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, ExpensesDataService.COLUMN_MAPPING, 
                params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(
                base_data, request, ExpensesDataService.COLUMN_MAPPING, 
                ExpensesDataService.COLUMN_FILTER_TYPES
            )
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand totals
            records_filtered = len(base_data)
            grand_totals = ExpensesDataService.calculate_grand_totals(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Calculate row count start
            row_count_start = DataTablesService.calculate_row_count_start(
                params['start'], params['length']
            )
            
            # Format final data
            final_data = ExpensesDataService.format_final_data(paginated_data, row_count_start)
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_totals': grand_totals
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in expenses_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'miamala/expenses.html')


@never_cache
@login_required
def expenses_actions(request: HttpRequest) -> JsonResponse:
    """Handle Expenses actions (add, update, delete, view)"""
    if request.method == 'POST':
        try:
            post_data = request.POST
            expense_edit = post_data.get('expense_edit')
            expense_delete = post_data.get('expense_delete')
            expense_view = post_data.get('expense_view')
            
            # Route to appropriate service method
            if expense_view:
                result = ExpensesService.view_expense(expense_view)
            elif expense_delete:
                result = ExpensesService.delete_expense(expense_delete)
            elif expense_edit:
                result = ExpensesService.update_expense(post_data, expense_edit, request.user)
            else:
                result = ExpensesService.create_expense(post_data, request.user)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in expenses_actions: {str(e)}")
            return JsonResponse({'success': False, 'sms': 'Operation failed..!'})
    
    return JsonResponse({'success': False, 'sms': 'Unknown error'})
