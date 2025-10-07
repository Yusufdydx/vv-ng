from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='courses_list'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('manage/', views.CourseManageView.as_view(), name='course_manage'),  # Add this line
    path('<int:pk>/approve/', views.approve_course, name='approve_course'),
    path('<int:pk>/reject/', views.reject_course, name='reject_course'),
]