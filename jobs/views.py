from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Job
from site_core.models import Category   # instead of JobCategory
from .forms import JobForm


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages

@staff_member_required
def approve_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = 'approved'
    job.save()
    messages.success(request, f"✅ Job '{job.title}' approved successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@staff_member_required
def reject_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = 'rejected'
    job.save()
    messages.error(request, f"❌ Job '{job.title}' rejected.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


class JobManageView(LoginRequiredMixin, ListView):
    model = Job
    template_name = 'jobs/manage.html'
    context_object_name = 'jobs'
    
    def get_queryset(self):
        return Job.objects.filter(posted_by=self.request.user).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = self.get_queryset()
        
        context.update({
            'approved_jobs': jobs.filter(status='approved').count(),
            'pending_jobs': jobs.filter(status='pending').count(),
            'rejected_jobs': jobs.filter(status='rejected').count(),
        })
        return context
    
    
class JobListView(ListView):
    model = Job
    template_name = 'jobs/list.html'
    context_object_name = 'jobs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Job.objects.filter(status='approved').select_related('posted_by', 'category')
        
        category = self.request.GET.get('category')
        job_type = self.request.GET.get('job_type')
        location = self.request.GET.get('location')
        level = self.request.GET.get('level')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__name=category)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if location:
            queryset = queryset.filter(location__icontains=location)
        if level:
            queryset = queryset.filter(level_requirement=level)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(company_name__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type="job", is_active=True)
        return context

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/detail.html'
    context_object_name = 'job'
    
    def get_object(self):
        obj = super().get_object()
        obj.increment_views()
        return obj

from django.contrib import messages
from django.urls import reverse_lazy

class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/create.html'
    
    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            '✅ Your job posting has been submitted for admin approval. You will be notified once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Please correct the errors below.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('jobs_list')

class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/edit.html'
    success_url = reverse_lazy('jobs_list')
    
    def test_func(self):
        job = self.get_object()
        return job.posted_by == self.request.user

class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Job
    template_name = 'jobs/delete.html'
    success_url = reverse_lazy('jobs_list')
    
    def test_func(self):
        job = self.get_object()
        return job.posted_by == self.request.user