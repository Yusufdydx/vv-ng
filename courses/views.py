from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Course, Enrollment, PromoCode
from .forms import CourseForm
from site_core.models import Category



from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages

@staff_member_required
def approve_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.status = 'approved'
    course.save()
    messages.success(request, f"✅ Course '{course.title}' approved successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/'))

@staff_member_required
def reject_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.status = 'rejected'
    course.save()
    messages.error(request, f"❌ Course '{course.title}' rejected.")
    return redirect(request.META.get('HTTP_REFERER', '/'))




class CourseListView(ListView):
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Course.objects.filter(status='approved').select_related('instructor', 'category')
        
        category = self.request.GET.get('category')
        level = self.request.GET.get('level')
        mode = self.request.GET.get('mode')
        search = self.request.GET.get('search')
        
        if category:
            queryset = queryset.filter(category__name=category)
        if level:
            queryset = queryset.filter(level=level)
        if mode:
            queryset = queryset.filter(mode=mode)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(category_type="course", is_active=True)
        return context

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'

from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/create.html'
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        form.instance.status = 'pending'
        response = super().form_valid(form)
        
        # Add success message
        messages.success(
            self.request, 
            '✅ Your course has been submitted for admin approval. You will be notified once approved.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ Please correct the errors below.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses_list')



class CourseManageView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/manage.html'
    context_object_name = 'courses'
    
    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user).select_related('category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_queryset()
        
        context.update({
            'approved_courses': courses.filter(status='approved').count(),
            'pending_courses': courses.filter(status='pending').count(),
            'rejected_courses': courses.filter(status='rejected').count(),
        })
        return context
    
    
class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/edit.html'
    success_url = reverse_lazy('courses_list')
    
    def test_func(self):
        course = self.get_object()
        return course.instructor == self.request.user