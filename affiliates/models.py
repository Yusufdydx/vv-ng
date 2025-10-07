from django.db import models
from django.conf import settings
from django.utils import timezone

class Referral(models.Model):
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['referrer', 'referred_user']

    def __str__(self):
        return f"{self.referrer.username} -> {self.referred_user.username}"

class AffiliateSale(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]

    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='sales')
    sale = models.ForeignKey('payments.Transaction', on_delete=models.CASCADE, related_name='affiliate_commissions')
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission percentage")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Affiliate Sale: {self.referral.referrer.username} - {self.commission_amount}"

    def mark_as_paid(self):
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()