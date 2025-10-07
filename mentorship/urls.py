from django.urls import path
from . import views

urlpatterns = [
    path('', views.MentorshipOfferListView.as_view(), name='mentorship_list'),
    path('<int:pk>/', views.MentorshipOfferDetailView.as_view(), name='mentorship_detail'),
    path('create/', views.MentorshipOfferCreateView.as_view(), name='mentorship_create'),
    path('<int:offer_id>/apply/', views.MentorshipApplicationCreateView.as_view(), name='mentorship_apply'),
    path('manage/', views.manage_mentorship, name='mentorship_manage'),
]