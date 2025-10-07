from django.contrib import admin
from .models import MentorshipOffer, MentorshipApplication

@admin.register(MentorshipOffer)
class MentorshipOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentor', 'expertise_area', 'price_per_hour', 'subscription_requirement', 'current_students', 'max_students', 'status', 'created_at')
    list_filter = ('status', 'subscription_requirement', 'expertise_area', 'created_at')
    search_fields = ('title', 'description', 'mentor__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_offers', 'reject_offers']
    
    def approve_offers(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} mentorship offers approved.')
    approve_offers.short_description = "Approve selected offers"
    
    def reject_offers(self, request, queryset):
        for offer in queryset:
            offer.status = 'rejected'
            offer.save()
        self.message_user(request, f'{queryset.count()} offers rejected.')
    reject_offers.short_description = "Reject selected offers"

@admin.register(MentorshipApplication)
class MentorshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('mentorship_offer', 'applicant', 'requested_duration', 'total_amount', 'status', 'applied_at', 'approved_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('mentorship_offer__title', 'applicant__username')
    readonly_fields = ('applied_at', 'approved_at', 'completed_at')
    actions = ['approve_applications', 'complete_applications']
    
    def approve_applications(self, request, queryset):
        for application in queryset:
            application.approve()
        self.message_user(request, f'{queryset.count()} applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def complete_applications(self, request, queryset):
        for application in queryset:
            application.complete()
        self.message_user(request, f'{queryset.count()} applications completed.')
    complete_applications.short_description = "Mark selected applications as completed"