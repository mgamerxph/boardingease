from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


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
    path('boardinghouse/<int:pk>/book/', views.book_boardinghouse, name='book_boardinghouse'),
    path('manual-booking/<int:bh_id>/', views.manual_booking, name='manual_booking'),
    path('owner/edit/<int:pk>/', views.edit_boardinghouse, name='edit_boardinghouse'),
    path('owner/delete/<int:pk>/', views.delete_boardinghouse, name='delete_boardinghouse'),
    path('booking/<int:booking_id>/approve/', views.approve_booking, name='approve_booking'),
    path('booking/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('guest/booking/<int:booking_id>/cancel/', views.cancel_booking_guest, name='cancel_booking_guest'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)