from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    # Owner details
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=15, blank=True)

    # ✅ New fields
    email = models.EmailField(blank=True)
    business_permit = models.ImageField(upload_to='business_permits/', blank=True, null=True)

    def __str__(self):
        return self.user.username

# ✅ Automatically create a Profile after a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class BoardingHouse(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)  # Owner (User)
    name = models.CharField(max_length=255)
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    image = models.ImageField(upload_to='boarding_images/', blank=True, null=True)  # ✅ Add this line
    is_booked = models.BooleanField(default=False)  # ✅ New field to track booking status

    def __str__(self):
        return self.name

# ✅ Booking model to store booking details
class Booking(models.Model):
    STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('cancelled', 'Cancelled'),
]

    boardinghouse = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # ✅
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.boardinghouse.name}"