from django.db import models
from django.conf import settings
from django.utils import timezone

class MentorshipOffer(models.Model):
    SUBSCRIPTION_REQUIREMENTS = [
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('mentorship', 'Mentorship'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_offers')
    title = models.CharField(max_length=200)
    description = models.TextField()
    expertise_area = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_requirement = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_REQUIREMENTS, 
        default='starter'
    )
    max_students = models.PositiveIntegerField(default=1)
    current_students = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.mentor.username}"

    def can_accept_more_students(self):
        return self.current_students < self.max_students

class MentorshipApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    mentorship_offer = models.ForeignKey(MentorshipOffer, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentorship_applications')
    requested_duration = models.PositiveIntegerField(help_text="Duration in hours")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    application_message = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.username} -> {self.mentorship_offer.title}"

    def save(self, *args, **kwargs):
        if not self.total_amount and self.requested_duration and self.mentorship_offer:
            self.total_amount = self.requested_duration * self.mentorship_offer.price_per_hour
        super().save(*args, **kwargs)

    def approve(self):
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()

    def complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()