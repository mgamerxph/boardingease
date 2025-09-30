from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from multiselectfield import MultiSelectField


# -----------------------------
# Profile Model
# -----------------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    # Owner details
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=15, blank=True)

    # Extra
    email = models.EmailField(blank=True)
    business_permit = models.ImageField(upload_to="business_permits/", blank=True, null=True)

    def __str__(self):
        return self.user.username


# ✅ Automatically create a Profile after a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# -----------------------------
# BoardingHouse Model (also acts as Room)
# -----------------------------
class BoardingHouse(models.Model):
    # Choices
    AMENITIES_CHOICES = [
        ("kitchen", "Kitchen Area"),
        ("comfort_room", "Comfort Room"),
        ("laundry", "Laundry Area"),
        ("balcony", "Balcony"),
        ("study", "Study Area"),
        ("cctv", "CCTV"),
        ("parking", "Parking Space"),
        ("lockable_gate", "Lockable Gate"),
        ("bedroom", "Bedroom"),
        ("cabinet", "Cabinet"),
    ]

    INCLUSION_CHOICES = [
        ("water", "Water Bill"),
        ("electric", "Electric Bill"),
        ("wifi", "WiFi Connection"),
    ]

    HOUSE_RULE_CHOICES = [
        ("curfew", "Curfew"),
        ("advance_payment", "Advance Payment"),
        ("deposit", "Deposit"),
        ("lady_only", "Lady Borders Only"),
        ("male_only", "Male Borders Only"),
        ("visitors_allowed", "Visitors Are Allowed"),
        ("appliances", "Additional Appliances"),
    ]

    # Relations
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Basic Info
    name = models.CharField(max_length=255)
    address = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Bedspacer / Regular Room
    is_bedspacer = models.BooleanField(default=False)  # ✅ True = shared occupancy
    capacity = models.PositiveIntegerField(default=1)  # ✅ How many tenants can stay

    # Conditional fields
    curfew_start = models.TimeField(blank=True, null=True)
    curfew_end = models.TimeField(blank=True, null=True)
    advance_months = models.PositiveIntegerField(default=0)
    deposit_months = models.PositiveIntegerField(default=0)

    # Images
    image = models.ImageField(upload_to="boarding_images/", blank=True, null=True)
    additional_photo = models.ImageField(upload_to="boarding_images/", blank=True, null=True)

    # Selections
    inclusions = MultiSelectField(choices=INCLUSION_CHOICES, blank=True)
    amenities = MultiSelectField(choices=AMENITIES_CHOICES, blank=True)
    house_rules = MultiSelectField(choices=HOUSE_RULE_CHOICES, blank=True)

    # Others
    other_inclusions = models.CharField(max_length=255, blank=True, null=True)
    other_amenities = models.CharField(max_length=255, blank=True, null=True)
    other_house_rules = models.CharField(max_length=255, blank=True, null=True)

    # Status
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def current_bookings(self):
        """Count approved bookings"""
        return self.bookings.filter(status="approved").count()

    @property
    def available_slots(self):
        """Available slots left (for bedspacer)"""
        return max(0, self.capacity - self.current_bookings)


# -----------------------------
# Booking Model
# -----------------------------
class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    boardinghouse = models.ForeignKey(
        'BoardingHouse',
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Guest info
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(default='example@example.com')  # New field for notification
    visit_date = models.DateField(null=True, blank=True)  # Optional visit date

    # Status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.boardinghouse.name}"