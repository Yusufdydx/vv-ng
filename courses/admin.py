from django.contrib import admin
from .models import CourseCategory, Course, Enrollment, PromoCode

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'course_count')
    list_filter = ('is_active',)
    search_fields = ('name',)
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'level', 'price', 'spots_left', 'status', 'created_at')
    list_filter = ('status', 'level', 'mode', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_courses', 'reject_courses']
    
    def approve_courses(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} courses approved successfully.')
    approve_courses.short_description = "Approve selected courses"
    
    def reject_courses(self, request, queryset):
        for course in queryset:
            course.status = 'rejected'
            course.save()
        self.message_user(request, f'{queryset.count()} courses rejected.')
    reject_courses.short_description = "Reject selected courses"

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'status', 'enrolled_at', 'final_price')
    list_filter = ('status', 'enrolled_at')
    search_fields = ('course__title', 'student__username')

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'discount_amount', 'used_count', 'max_uses', 'is_active', 'valid_until')
    list_filter = ('is_active',)
    search_fields = ('code',)