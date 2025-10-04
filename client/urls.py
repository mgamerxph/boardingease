from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('boardinghouse/<int:pk>/', views.boardinghouse_detail, name='boardinghouse_detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/add/', views.add_boardinghouse, name='add_boardinghouse'),
    path('pending-bookings/', views.pending_bookings_view, name='pending_bookings'),
    path('register/owner/', views.register_owner, name='register_owner'),
    path('register/pending/', views.registration_pending, name='registration_pending'),
    path('manual-booking/<int:bh_id>/', views.manual_booking, name='manual_booking'),
    path('owner/edit/<int:pk>/', views.edit_boardinghouse, name='edit_boardinghouse'),
    path('owner/delete/<int:pk>/', views.delete_boardinghouse, name='delete_boardinghouse'),
    path('booking/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('booking/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('guest/booking/<int:booking_id>/cancel/', views.cancel_booking_guest, name='cancel_booking_guest'),
    path('booking/<int:booking_id>/edit/', views.edit_booking, name='edit_booking'),
    path('owner/tenants/<int:house_id>/', views.tenants_view, name='tenants_view'),
    path("live-search/", views.live_search, name="live_search"),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='password_reset.html'), 
         name='password_reset'),

    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), 
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), 
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), 
         name='password_reset_complete'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)