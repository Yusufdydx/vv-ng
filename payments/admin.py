from django.contrib import admin
from .models import PaymentMethod, Transaction

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'user', 'transaction_type', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = ('reference', 'user__username', 'description')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'completed_at')
    actions = ['approve_transactions', 'reject_transactions']
    
    def approve_transactions(self, request, queryset):
        approved_count = 0
        for transaction in queryset.filter(status='pending'):
            if transaction.approve():
                approved_count += 1
        self.message_user(request, f'{approved_count} transactions approved.')
    approve_transactions.short_description = "Approve selected transactions"
    
    def reject_transactions(self, request, queryset):
        for transaction in queryset:
            transaction.reject("Rejected by admin")
        self.message_user(request, f'{queryset.count()} transactions rejected.')
    reject_transactions.short_description = "Reject selected transactions"