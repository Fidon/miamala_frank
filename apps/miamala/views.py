import zoneinfo
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse
from django.http import JsonResponse
from decimal import Decimal
from .models import Selcompay, Lipanamba, Debts, Loans
from utils.util_functions import admin_required, conv_timezone, filter_items, format_number, selcom_profit, lipa_profit



# SelcomPay transactions page
@never_cache
@login_required
@admin_required()
def selcom_transactions_page(request):
    if request.method == "POST":
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')

        # Base queryset
        queryset = Selcompay.objects.filter(deleted=False)

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date, parsed_end_date = None, None
        
        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for transact in queryset:
            base_data.append({
                'id': transact.id,
                'dates': transact.created_at,
                'names': transact.name,
                'amount': transact.amount,
                'profit': selcom_profit(transact.amount),
                'describe': transact.description if transact.description else ""
            })

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'dates',
            2: 'names',
            3: 'amount',
            4: 'profit',
        }

        # Filter types for specific columns
        column_filter_types = {
            'profit': 'numeric',
            'amount': 'numeric',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'dates')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    base_data = [
                        item for item in base_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]
        
        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Calculate grand totals before pagination
        total_amount = sum(item['amount'] for item in base_data)
        total_profit = sum(item['profit'] for item in base_data)
        grand_totals = {
            'total_amount': '{:,.2f}'.format(total_amount),
            'total_profit': '{:,.2f}'.format(total_profit),
        }

        # Apply pagination
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'profit': format_number(item.get('profit')),
                'describe': item.get('describe'),
                'action': ""
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_totals': grand_totals
        }
        return JsonResponse(ajax_response)
    return render(request, 'miamala/selcom.html')


# Selcompay actions eg. add new, update & delete
@never_cache
@login_required
@admin_required()
def selcom_transactions_actions(request):
    if request.method == 'POST':
        try:
            trans_names = request.POST.get('names')
            trans_amount = request.POST.get('amount')
            trans_describe = request.POST.get('describe')
            trans_id = request.POST.get('transact_id')
            delete_id = request.POST.get('delete_id')
            if delete_id:
                transaction = Selcompay.objects.get(id=delete_id)
                transaction.deleted = 1
                transaction.save()
                fdback = 'Transaction deleted successfully!'
            elif trans_id:
                transaction = Selcompay.objects.get(id=trans_id)
                trans_describe = trans_describe.strip() if not trans_describe.strip() == "" else None
                trans_names = trans_names.strip()

                if len(trans_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                if not transaction.name == trans_names:
                    transaction.names = trans_names
                if not transaction.amount == trans_amount:
                    transaction.amount = trans_amount
                if not transaction.description == trans_describe:
                    transaction.description = trans_describe
                transaction.save()
                fdback = 'Transaction updated successfully!'
            else:
                trans_describe = trans_describe.strip() if not trans_describe.strip() == "" else None
                trans_names = trans_names.strip()

                if len(trans_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                transaction = Selcompay(
                    name=trans_names,
                    amount=trans_amount,
                    description=trans_describe
                )
                transaction.save()
                fdback = 'Transaction added successfully!'
            return JsonResponse({'success': True, 'sms': fdback})
        except Exception as ex_sms:
            return JsonResponse({'success': False, 'sms': ex_sms})


# lipanamba transactions page
@never_cache
@login_required
@admin_required()
def lipa_transactions_page(request):
    if request.method == "POST":
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')

        # Base queryset
        queryset = Lipanamba.objects.filter(deleted=False)

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date, parsed_end_date = None, None
        
        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for transact in queryset:
            base_data.append({
                'id': transact.id,
                'dates': transact.created_at,
                'names': transact.name,
                'amount': transact.amount,
                'profit': lipa_profit(transact.amount),
                'describe': transact.description if transact.description else ""
            })

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'dates',
            2: 'names',
            3: 'amount',
            4: 'profit',
            5: 'describe'
        }

        # Filter types for specific columns
        column_filter_types = {
            'profit': 'numeric',
            'amount': 'numeric',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'dates')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    base_data = [
                        item for item in base_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Calculate grand totals before pagination
        total_amount = sum(item['amount'] for item in base_data)
        total_profit = sum(item['profit'] for item in base_data)
        grand_totals = {
            'total_amount': format_number(total_amount),
            'total_profit': format_number(total_profit),
        }

        # Apply pagination
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'profit': format_number(item.get('profit')),
                'describe': item.get('describe'),
                'action': ""
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_totals': grand_totals
        }
        return JsonResponse(ajax_response)
    return render(request, 'miamala/lipanamba.html')


# Lipanamba actions eg. add new, update & delete
@never_cache
@login_required
@admin_required()
def lipanamba_transactions_actions(request):
    if request.method == 'POST':
        try:
            trans_names = request.POST.get('names')
            trans_amount = request.POST.get('amount')
            trans_describe = request.POST.get('describe')
            trans_id = request.POST.get('transact_id')
            delete_id = request.POST.get('delete_id')
            if delete_id:
                transaction = Lipanamba.objects.get(id=delete_id)
                transaction.deleted = 1
                transaction.save()
                fdback = 'Transaction deleted successfully!'
            elif trans_id:
                trans_describe = trans_describe.strip() if not trans_describe.strip() == "" else None
                transaction = Lipanamba.objects.get(id=trans_id)
                trans_names = trans_names.strip()
                if len(trans_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                if not transaction.name == trans_names:
                    transaction.name = trans_names
                if not transaction.amount == trans_amount:
                    transaction.amount = trans_amount
                if not transaction.description == trans_describe:
                    transaction.description = trans_describe
                transaction.save()
                fdback = 'Transaction updated successfully!'
            else:
                trans_describe = trans_describe.strip() if not trans_describe.strip() == "" else None
                trans_names = trans_names.strip()
                if len(trans_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                transaction = Lipanamba (
                    name = trans_names,
                    amount = trans_amount,
                    description = trans_describe
                )
                transaction.save()
                fdback = 'Transaction added successfully!'
            return JsonResponse({'success': True, 'sms': fdback})
        except Exception as ex_sms:
            return JsonResponse({'success': False, 'sms': 'Operation failed'})


# Debts page
@never_cache
@login_required
@admin_required()
def debts_page(request):
    if request.method == "POST":
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')

        # Base queryset
        queryset = Debts.objects.filter(deleted=False)

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date, parsed_end_date = None, None
        
        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for debt in queryset:
            base_data.append({
                'id': debt.id,
                'dates': debt.created_at,
                'names': debt.name,
                'amount': debt.amount,
                'paid': debt.paid,
                'balance': debt.amount - debt.paid,
                'describe': debt.description if debt.description else ""
            })

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'dates',
            2: 'names',
            3: 'amount',
            4: 'paid',
            5: 'balance',
            6: 'describe'
        }

        # Filter types for specific columns
        column_filter_types = {
            'paid': 'numeric',
            'amount': 'numeric',
            'balance': 'numeric',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'dates')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    base_data = [
                        item for item in base_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Calculate grand totals before pagination
        total_amount = sum(item['amount'] for item in base_data)
        total_paid = sum(item['paid'] for item in base_data)
        total_balance = sum(item['balance'] for item in base_data)
        grand_totals = {
            'total_amount': format_number(total_amount),
            'total_paid': format_number(total_paid),
            'total_balance': format_number(total_balance),
        }

        # Apply pagination
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'paid': format_number(item.get('paid')),
                'balance': format_number(item.get('balance')),
                'describe': item.get('describe'),
                'action': ""
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_totals': grand_totals
        }
        return JsonResponse(ajax_response)
    return render(request, 'miamala/debts.html')


# Add, Update & Delete debts
@never_cache
@login_required
@admin_required()
def debts_actions(request):
    if request.method == 'POST':
        try:
            debt_names = request.POST.get('names')
            debt_amount = request.POST.get('amount')
            debt_paid = request.POST.get('paid')
            if debt_paid:
                debt_paid = Decimal(debt_paid)
            debt_describe = request.POST.get('describe')
            debt_id = request.POST.get('debt_id')
            delete_id = request.POST.get('delete_id')
            if delete_id:
                debt = Debts.objects.get(id=delete_id)
                debt.deleted = 1
                debt.save()
                fdback = 'Debt deleted successfully!'
            elif debt_id:
                debt_describe = debt_describe if not debt_describe.strip() == "" else None
                actual_debt = Debts.objects.get(id=debt_id)
                debt_names = debt_names.strip()

                if len(debt_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})

                if debt_paid < 0.0:
                    actual_debt.paid = actual_debt.paid + abs(debt_paid)
                else:
                    actual_debt.amount = actual_debt.amount + debt_paid
                
                if not actual_debt.name == debt_names:
                    actual_debt.name = debt_names
                if not actual_debt.description == debt_describe:
                    actual_debt.description = debt_describe

                actual_debt.save()
                fdback = 'Debt details updated successfully!'
            else:
                debt_names = debt_names.strip()
                if len(debt_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                new_debt = Debts (
                    name=debt_names,
                    amount=debt_amount,
                    description=debt_describe if debt_describe else None
                )
                new_debt.save()
                fdback = 'New debt added successfully!'
            return JsonResponse({'success': True, 'sms': fdback})
        except Exception as ex_sms:
            return JsonResponse({'success': False, 'sms': 'Operation failed..!'})


# Loans page
@never_cache
@login_required
def loans_page(request):
    if request.method == "POST":
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 1))
        order_dir = request.POST.get('order[0][dir]', 'desc')

        # Base queryset
        queryset = Loans.objects.filter(deleted=False)

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date, parsed_end_date = None, None
        
        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
        
        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for loan in queryset:
            base_data.append({
                'id': loan.id,
                'dates': loan.created_at,
                'names': loan.name,
                'amount': loan.amount,
                'paid': loan.paid,
                'balance': loan.amount - loan.paid,
                'describe': loan.description if loan.description else ""
            })

        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'dates',
            2: 'names',
            3: 'amount',
            4: 'paid',
            5: 'balance',
            6: 'describe'
        }

        # Filter types for specific columns
        column_filter_types = {
            'paid': 'numeric',
            'amount': 'numeric',
            'balance': 'numeric',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'dates')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    base_data = [
                        item for item in base_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Calculate grand totals before pagination
        total_amount = sum(item['amount'] for item in base_data)
        total_paid = sum(item['paid'] for item in base_data)
        total_balance = sum(item['balance'] for item in base_data)
        grand_totals = {
            'total_amount': format_number(total_amount),
            'total_paid': format_number(total_paid),
            'total_balance': format_number(total_balance),
        }

        # Apply pagination
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'dates': conv_timezone(item.get('dates'), '%d-%b-%Y %H:%M'),
                'names': item.get('names'),
                'amount': format_number(item.get('amount')),
                'paid': format_number(item.get('paid')),
                'balance': format_number(item.get('balance')),
                'describe': item.get('describe'),
                'action': ""
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_totals': grand_totals
        }
        return JsonResponse(ajax_response)
    return render(request, 'miamala/loans.html')


# Add, Update & Delete loans
@never_cache
@login_required
def loans_actions(request):
    if request.method == 'POST':
        try:
            loan_names = request.POST.get('names')
            loan_amount = request.POST.get('amount')
            loan_paid = request.POST.get('paid')
            if loan_paid:
                loan_paid = Decimal(loan_paid)
            loan_describe = request.POST.get('describe')
            loan_id = request.POST.get('loan_id')
            delete_id = request.POST.get('delete_id')
            if delete_id:
                loan = Loans.objects.get(id=delete_id)
                loan.deleted = 1
                loan.save()
                fdback = 'Loan deleted successfully!'
            elif loan_id:
                loan_describe = loan_describe.strip() if not loan_describe.strip() == "" else None
                actual_loan = Loans.objects.get(id=loan_id)
                loan_names = loan_names.strip()

                if len(loan_names) < 3:
                    return JsonResponse({'success': False, 'sms': 'Names must have atleast 3 characters.'})
                
                if loan_paid < 0.0:
                    actual_loan.paid = actual_loan.paid + abs(loan_paid)
                else:
                    actual_loan.amount = actual_loan.amount + loan_paid
                
                if not actual_loan.name == loan_names:
                    actual_loan.name = loan_names
                if not actual_loan.description == loan_describe:
                    actual_loan.description = loan_describe
                    
                actual_loan.save()
                fdback = 'Loan details updated successfully!'
            else:
                loan_describe = loan_describe.strip() if not loan_describe.strip() == "" else None
                loan_names = loan_names.strip()

                new_loan = Loans (
                    name = loan_names,
                    amount = loan_amount,
                    description = loan_describe
                )
                new_loan.save()
                fdback = 'New loan added successfully!'
            return JsonResponse({'success': True, 'sms': fdback})
        except Exception as ex_sms:
            return JsonResponse({'success': False, 'sms': ex_sms})


