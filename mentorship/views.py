from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import MentorshipOffer, MentorshipApplication
from .forms import MentorshipOfferForm, MentorshipApplicationForm
from payments.models import Transaction
from site_core.models import SiteSetting
from django.contrib.auth.decorators import login_required

class MentorshipOfferListView(ListView):
    model = MentorshipOffer
    template_name = 'mentorship/list.html'
    context_object_name = 'offers'
    paginate_by = 20
    
    def get_queryset(self):
        return MentorshipOffer.objects.filter(
            status='approved', 
            is_available=True
        ).select_related('mentor')

class MentorshipOfferDetailView(DetailView):
    model = MentorshipOffer
    template_name = 'mentorship/detail.html'
    context_object_name = 'offer'

class MentorshipOfferCreateView(LoginRequiredMixin, CreateView):
    model = MentorshipOffer
    form_class = MentorshipOfferForm
    template_name = 'mentorship/create.html'
    success_url = reverse_lazy('mentorship_list')
    
    def form_valid(self, form):
        form.instance.mentor = self.request.user
        form.instance.status = 'pending'
        return super().form_valid(form)

class MentorshipApplicationCreateView(LoginRequiredMixin, CreateView):
    model = MentorshipApplication
    form_class = MentorshipApplicationForm
    template_name = 'mentorship/apply.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.mentorship_offer = get_object_or_404(MentorshipOffer, pk=self.kwargs['offer_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentorship_offer'] = self.mentorship_offer
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            form.instance.mentorship_offer = self.mentorship_offer
            form.instance.applicant = self.request.user
            
            site_settings = SiteSetting.get_solo()
            total_amount = form.instance.total_amount
            admin_fee = total_amount * (site_settings.mentorship_fee_pct / 100)
            net_amount = total_amount - admin_fee
            
            response = super().form_valid(form)
            
            Transaction.objects.create(
                user=self.request.user,
                amount=total_amount,
                transaction_type='MENTORSHIP_PAYMENT',
                status='pending',
                description=f"Mentorship application for {self.mentorship_offer.title}",
                metadata={
                    'mentorship_application_id': form.instance.id,
                    'mentor_id': self.mentorship_offer.mentor.id,
                    'admin_fee': float(admin_fee),
                    'net_amount': float(net_amount),
                }
            )
            
            return response
    
    def get_success_url(self):
        return reverse_lazy('mentorship_application_detail', kwargs={'pk': self.object.pk})

@login_required
def manage_mentorship(request):
    user = request.user
    
    if request.user.subscription_level == 'mentorship':
        offers = MentorshipOffer.objects.filter(mentor=user)
        applications = MentorshipApplication.objects.filter(mentorship_offer__mentor=user)
    else:
        offers = MentorshipOffer.objects.none()
        applications = MentorshipApplication.objects.filter(applicant=user)
    
    context = {
        'offers': offers,
        'applications': applications,
    }
    
    return render(request, 'mentorship/manage.html', context)