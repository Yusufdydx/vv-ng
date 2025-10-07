from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib import messages
from .models import Transaction, PaymentMethod
from .forms import AddMoneyForm, WithdrawForm, TransferForm
from site_core.models import SiteSetting
from .forms_manual import ManualDepositForm
from .models import ManualDeposit
from site_core.models import SiteSetting
from django.contrib import messages

@login_required
def manual_deposit(request):
    site_settings = SiteSetting.get_solo()
    
    if request.method == 'POST':
        form = ManualDepositForm(request.POST, request.FILES)
        if form.is_valid():
            manual_deposit = form.save(commit=False)
            manual_deposit.user = request.user
            manual_deposit.save()
            
            messages.success(
                request, 
                "Manual deposit submitted! We'll review it within 24 hours and credit your account."
            )
            return redirect('transactions_list')
    else:
        form = ManualDepositForm()

    context = {
        'form': form,
        'site_settings': site_settings,
        'manual_account': {
            'bank_name': site_settings.manual_payment_bank_name,
            'account_number': site_settings.manual_payment_account_number,
            'account_name': site_settings.manual_payment_account_name,
        }
    }
    return render(request, 'payments/manual_deposit.html', context)

@login_required
def manual_deposit_list(request):
    deposits = ManualDeposit.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'deposits': deposits,
    }
    return render(request, 'payments/manual_deposit_list.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.utils import IntegrityError
from .models import PaymentMethod, Transaction
from site_core.models import SiteSetting
from .forms import AddMoneyForm
import uuid


# /vinaji_project/payments/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .models import PaymentMethod, ManualDeposit, Transaction
from .forms import ManualDepositForm # Import the form
from accounts.models import VirtualAccount
from site_core.models import SiteSetting

@login_required
def add_money(request):
    user = request.user
    site_settings = SiteSetting.get_solo()
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    # Get user's primary virtual account for the 'auto' method display
    primary_virtual_account = VirtualAccount.objects.filter(
        user=user, is_primary=True, is_active=True
    ).first()

    # Form for manual deposit submission
    manual_form = ManualDepositForm()

    if request.method == 'POST':
        selected = request.POST.get('payment_method', '')
        if not selected:
            messages.error(request, "Please select a payment method.")
            return redirect('add_money')

        # Split the value to get ID and type
        method_parts = selected.split('_')
        if len(method_parts) != 2:
            messages.error(request, "Invalid payment method selected.")
            return redirect('add_money')

        method_id, method_type = method_parts
        try:
            method_id = int(method_id)
        except ValueError:
            messages.error(request, "Invalid payment method ID.")
            return redirect('add_money')

        payment_method = get_object_or_404(PaymentMethod, id=method_id)

        if method_type == 'manual':
            manual_form = ManualDepositForm(request.POST, request.FILES)
            if manual_form.is_valid():
                deposit = manual_form.save(commit=False)
                deposit.user = user
                deposit.save()
                messages.success(
                    request,
                    "Your manual deposit proof has been submitted successfully. It will be reviewed shortly."
                )
                return redirect('transactions_list')
            else:
                messages.error(request, "Please correct the errors in the manual deposit form.")

        elif method_type == 'auto':
            # You can trigger your auto payment flow here if needed
            messages.info(request, "Automatic deposit selected. Use your virtual account to fund your wallet.")

    context = {
        'payment_methods': payment_methods,
        'site_settings': site_settings,
        'manual_form': manual_form,
        'manual_bank_details': {
            'name': site_settings.manual_bank_name,
            'number': site_settings.manual_account_number,
            'account_name': site_settings.manual_account_name,
        },
        'primary_virtual_account': primary_virtual_account,
        'current_balance': Transaction.get_user_balance(user),
    }
    return render(request, 'payments/add_money.html', context)




@login_required
def withdraw_money(request):
    if request.method == 'POST':
        form = WithdrawForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            current_balance = Transaction.get_user_balance(request.user)
            
            if amount > current_balance:
                messages.error(request, 'Insufficient balance for withdrawal.')
            else:
                transaction = form.save(commit=False)
                transaction.user = request.user
                transaction.transaction_type = 'withdraw'
                
                site_settings = SiteSetting.get_solo()
                if site_settings.withdraw_fee_pct > 0:
                    fee = transaction.amount * (site_settings.withdraw_fee_pct / 100)
                    transaction.metadata = {'admin_fee': float(fee)}
                
                transaction.save()
                messages.success(request, 'Withdrawal request submitted successfully.')
                return redirect('transactions_list')
    else:
        form = WithdrawForm()
    
    current_balance = Transaction.get_user_balance(request.user)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'current_balance': current_balance,
        'payment_methods': payment_methods,
    }
    return render(request, 'payments/withdraw.html', context)

@login_required
def transfer_money(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            recipient = form.cleaned_data['recipient_username']
            description = form.cleaned_data.get('description', '')
            
            current_balance = Transaction.get_user_balance(request.user)
            
            if amount > current_balance:
                messages.error(request, 'Insufficient balance for transfer.')
            else:
                with db_transaction.atomic():
                    site_settings = SiteSetting.get_solo()
                    fee = amount * (site_settings.transfer_fee_pct / 100)
                    net_amount = amount - fee
                    
                    # Create debit transaction for sender
                    debit_txn = Transaction.objects.create(
                        user=request.user,
                        amount=amount,
                        transaction_type='transfer',
                        status='completed',
                        description=f"Transfer to {recipient.username}: {description}",
                        metadata={
                            'recipient_id': recipient.id,
                            'admin_fee': float(fee),
                            'net_amount': float(net_amount)
                        }
                    )
                    
                    # Create credit transaction for recipient
                    credit_txn = Transaction.objects.create(
                        user=recipient,
                        amount=net_amount,
                        transaction_type='transfer',
                        status='completed',
                        description=f"Transfer from {request.user.username}: {description}",
                        metadata={
                            'sender_id': request.user.id,
                            'original_amount': float(amount),
                            'admin_fee': float(fee)
                        }
                    )
                    
                    # Create admin fee transaction
                    if fee > 0:
                        Transaction.objects.create(
                            user=request.user,  # Or system user
                            amount=fee,
                            transaction_type='admin_fee',
                            status='completed',
                            description=f"Transfer fee for transaction {debit_txn.reference}",
                            metadata={
                                'original_transaction_id': debit_txn.id
                            }
                        )
                
                messages.success(request, f'Transfer of {amount} to {recipient.username} completed successfully.')
                return redirect('transactions_list')
    else:
        form = TransferForm()
    
    current_balance = Transaction.get_user_balance(request.user)
    context = {
        'form': form,
        'current_balance': current_balance,
    }
    return render(request, 'payments/transfer.html', context)