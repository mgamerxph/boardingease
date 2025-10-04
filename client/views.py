from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import JsonResponse

from .models import BoardingHouse, Profile, Booking
from .forms import BoardingHouseForm, OwnerRegistrationForm, BookingForm


def home(request):
    query = request.GET.get('q', '')  # Search input
    bedspacer = request.GET.get('bedspacer', '')
    gender = request.GET.get('gender', '')

    selected_amenities = request.GET.get('amenities', '')
    selected_inclusions = request.GET.get('inclusions', '')
    selected_house_rules = request.GET.get('house_rules', '')

    # Start with all boarding houses
    boardinghouses = BoardingHouse.objects.all()

    # 🔍 Filter by search query (address)
    if query:
        boardinghouses = boardinghouses.filter(address__icontains=query)

    # 🛏 Filter by bedspacer
    if bedspacer == 'yes':
        boardinghouses = boardinghouses.filter(is_bedspacer=True)
    elif bedspacer == 'no':
        boardinghouses = boardinghouses.filter(is_bedspacer=False)

    # 🚻 Filter by gender
    if gender == 'male':
        boardinghouses = boardinghouses.filter(gender='male')
    elif gender == 'female':
        boardinghouses = boardinghouses.filter(gender='female')

    # 🏷 Filter by amenities
    if selected_amenities:
        boardinghouses = boardinghouses.filter(amenities__contains=selected_amenities)

    # 💡 Filter by inclusions
    if selected_inclusions:
        boardinghouses = boardinghouses.filter(inclusions__contains=selected_inclusions)

    # 📜 Filter by house rules
    if selected_house_rules:
        boardinghouses = boardinghouses.filter(house_rules__contains=selected_house_rules)

    # ✅ Session-based booking tracking (no login required)
    session_booked = request.session.get("booked_boardinghouses", [])

    for bh in boardinghouses:
        # check if any approved booking exists (overall "taken" flag)
        latest_booking = Booking.objects.filter(boardinghouse=bh).order_by("-id").first()
        bh.is_booked = latest_booking and latest_booking.status == "approved"

        # default flags
        bh.is_pending_for_this_user = False
        bh.pending_booking_id = None
        bh.is_approved_for_this_user = False

        # check this session’s booking instead of logged-in user
        if str(bh.id) in session_booked:
            user_booking = Booking.objects.filter(boardinghouse=bh).order_by("-id").first()
            if user_booking:
                if user_booking.status == "pending":
                    bh.is_pending_for_this_user = True
                    bh.pending_booking_id = user_booking.id
                elif user_booking.status == "approved":
                    bh.is_approved_for_this_user = True

    # Send everything to template
    context = {
        'boardinghouses': boardinghouses,
        'query': query,
        'bedspacer': bedspacer,
        'gender': gender,
        'selected_amenities': selected_amenities,
        'selected_inclusions': selected_inclusions,
        'selected_house_rules': selected_house_rules,
        'amenities_choices': BoardingHouse.AMENITIES_CHOICES,
        'inclusion_choices': BoardingHouse.INCLUSION_CHOICES,
        'house_rule_choices': BoardingHouse.HOUSE_RULE_CHOICES,
    }

    return render(request, 'home.html', context)


    return render(request, 'home.html', context)

def live_search(request):
    query = request.GET.get("q", "")
    bedspacer = request.GET.get("bedspacer", "")
    amenities = request.GET.get("amenities", "")
    inclusions = request.GET.get("inclusions", "")
    house_rules = request.GET.get("house_rules", "")

    boardinghouses = BoardingHouse.objects.all()

    # 🔎 Filter by address
    if query:
        boardinghouses = boardinghouses.filter(address__icontains=query)

    # 🛏️ Filter by bedspacer
    if bedspacer == "yes":
        boardinghouses = boardinghouses.filter(is_bedspacer=True)
    elif bedspacer == "no":
        boardinghouses = boardinghouses.filter(is_bedspacer=False)

    # 🏷️ Optional filters
    if amenities:
        boardinghouses = boardinghouses.filter(amenities__icontains=amenities)
    if inclusions:
        boardinghouses = boardinghouses.filter(inclusions__icontains=inclusions)
    if house_rules:
        boardinghouses = boardinghouses.filter(house_rules__icontains=house_rules)

    # Render partial with request context
    html = render_to_string(
        "partials/boardinghouse_list.html",
        {"boardinghouses": boardinghouses},
        request=request
    )

    return JsonResponse({"html": html})



def cancel_booking_guest(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, status='pending')

    # Remove booking and session mark
    booking.delete()

    booked_bhs = request.session.get('booked_boardinghouses', [])
    if str(booking.boardinghouse.id) in booked_bhs:
        booked_bhs.remove(str(booking.boardinghouse.id))
        request.session['booked_boardinghouses'] = booked_bhs

    messages.success(request, "Your booking has been cancelled.")
    return redirect('home')

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, boardinghouse__owner=request.user)
    booking.status = 'cancelled'  # Make sure this status is not 'approved'
    booking.save()
    messages.info(request, "Booking Canceled.")
    return redirect('owner_dashboard')

@login_required
def owner_dashboard(request):
    if not request.user.profile.is_owner:
        return redirect('home')

    # Filter param from URL
    status_filter = request.GET.get('status')

    # All BHs by owner
    boardinghouses = BoardingHouse.objects.filter(owner=request.user)

    # Booking stats
    all_bookings = Booking.objects.filter(boardinghouse__in=boardinghouses)
    total_bookings = all_bookings.count()
    approved_count = all_bookings.filter(status='approved').count()
    pending_count = all_bookings.filter(status='pending').count()
    rejected_count = all_bookings.filter(status='rejected').count()
    cancelled_count = all_bookings.filter(status='cancelled').count()

    # Total listings count
    total_listings = boardinghouses.count()

    # Attach extra data per boardinghouse
    for bh in boardinghouses:
        if bh.is_bedspacer:
            # All approved tenants for bedspacer
            bh.approved_bookings = Booking.objects.filter(
                boardinghouse=bh,
                status='approved'
            )
            # Remaining slots
            bh.remaining_slots = max(0, bh.capacity - bh.current_bookings)

        else:
            # For regular rooms, only allow one approved booking
            bh.approved_booking = Booking.objects.filter(
                boardinghouse=bh,
                status='approved'
            ).first()

        # Common: check if pending requests exist
        bh.has_pending = Booking.objects.filter(
            boardinghouse=bh,
            status='pending'
        ).exists()

    # Optional filter by status
    filtered_bookings = None
    valid_statuses = ['approved', 'pending', 'rejected', 'cancelled']
    if status_filter in valid_statuses:
        filtered_bookings = Booking.objects.filter(
            boardinghouse__in=boardinghouses,
            status=status_filter
        ).order_by('-id')

    return render(request, 'owner_dashboard.html', {
        'boardinghouses': boardinghouses,
        'filtered_bookings': filtered_bookings,
        'status_filter': status_filter,

        # 🆕 Analytics Data
        'total_listings': total_listings,
        'total_bookings': total_bookings,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'cancelled_count': cancelled_count,
    })

@login_required
def pending_bookings_view(request):
    if not request.user.profile.is_owner:
        return redirect('home')

    # Get all BHs owned by this user
    boardinghouses = BoardingHouse.objects.filter(owner=request.user)

    # Get filters from query string
    selected_bh = request.GET.get('boardinghouse')
    sort_order = request.GET.get('order', 'newest')  # default is newest

    # Base queryset: all pending bookings of this owner's BHs
    all_pending = Booking.objects.filter(
        boardinghouse__in=boardinghouses,
        status='pending'
    )

    # Filter by specific BH if selected
    if selected_bh:
        all_pending = all_pending.filter(room__boardinghouse__id=selected_bh)

    # Apply sort order
    if sort_order == 'oldest':
        all_pending = all_pending.order_by('created_at')
    else:
        all_pending = all_pending.order_by('-created_at')

    # Pagination
    paginator = Paginator(all_pending, 5)
    page_number = request.GET.get('page')
    pending_bookings = paginator.get_page(page_number)

    # Add "has_other_pending" flag
    for booking in pending_bookings:
        booking.has_other_pending = Booking.objects.filter(
            boardinghouse=booking.boardinghouse,
            status='pending'
        ).exclude(id=booking.id).exists()

    return render(request, 'pending_bookings.html', {
        'pending_bookings': pending_bookings,
        'boardinghouses': boardinghouses,
        'selected_bh': selected_bh,
        'current_order': sort_order,
    })

@login_required
def add_boardinghouse(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if not profile.is_owner:
        messages.warning(request, "Only owners can add boarding houses.")
        return redirect('home')

    if request.method == 'POST':
        form = BoardingHouseForm(request.POST, request.FILES)

        if form.is_valid():
            bh = form.save(commit=False)
            bh.owner = request.user
            bh.save()

            messages.success(request, "Boarding house added successfully.")
            return redirect('owner_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BoardingHouseForm()

    return render(request, 'add_boardinghouse.html', {
        'form': form,
    })

def register_owner(request):
    if request.method == 'POST':
        form = OwnerRegistrationForm(request.POST, request.FILES)  # ✅ include request.FILES
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Save to Profile
            profile = user.profile
            profile.is_owner = True
            profile.first_name = form.cleaned_data['first_name']
            profile.last_name = form.cleaned_data['last_name']
            profile.address = form.cleaned_data['address']
            profile.contact_number = form.cleaned_data['contact_number']
            profile.email = form.cleaned_data['email']  # ✅ Save email
            profile.business_permit = form.cleaned_data.get('business_permit')  # ✅ Save file
            profile.save()

            return redirect('registration_pending')
    else:
        form = OwnerRegistrationForm()
    return render(request, 'register_owner.html', {'form': form})

def registration_pending(request):
    return render(request, 'registration_pending.html')

@login_required
def edit_boardinghouse(request, pk):
    bh = get_object_or_404(BoardingHouse, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = BoardingHouseForm(request.POST, request.FILES, instance=bh)
        if form.is_valid():
            form.save()
            messages.success(request, "Boarding house updated successfully.")
            return redirect('owner_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BoardingHouseForm(instance=bh)
    return render(request, 'edit_boardinghouse.html', {'form': form})

@login_required
def delete_boardinghouse(request, pk):
    bh = get_object_or_404(BoardingHouse, pk=pk, owner=request.user)
    if request.method == 'POST':
        bh.delete()
        messages.success(request, "Boarding house deleted successfully.")
        return redirect('owner_dashboard')
    return render(request, 'confirm_delete.html', {'bh': bh})

def boardinghouse_detail(request, pk):
    bh = get_object_or_404(BoardingHouse, pk=pk)
    session_booked = request.session.get('booked_boardinghouses', [])
    bh_id_str = str(bh.id)

    user_booking = None
    booking_status = None

    # ✅ Handle booking form submission
    if request.method == "POST":
        # Prevent duplicate booking
        if bh_id_str in session_booked:
            messages.warning(
                request,
                "You’ve already booked this boarding house. Please wait for approval.",
                extra_tags='booking'
            )
            return redirect('boardinghouse_detail', pk=pk)

        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.boardinghouse = bh
            booking.status = "pending"
            # 🔹 No tenant field here since not logged in
            booking.save()

            # Save in session to prevent repeat booking
            session_booked.append(bh_id_str)
            request.session['booked_boardinghouses'] = session_booked

            messages.success(
                request,
                "Boarding house booked successfully. Please wait for approval.",
                extra_tags='booking'
            )
            return redirect("home")
        else:
            messages.error(
                request,
                "Please correct the errors below.",
                extra_tags='booking'
            )
    else:
        form = BookingForm()

    # ✅ Check existing booking status
    if bh_id_str in session_booked:
        user_booking = Booking.objects.filter(boardinghouse=bh).order_by("-id").first()
        if user_booking:
            booking_status = user_booking.status

            # Remove from session if booking was rejected/cancelled
            if booking_status in ["rejected", "cancelled"]:
                session_booked.remove(bh_id_str)
                request.session["booked_boardinghouses"] = session_booked
                booking_status = None

    return render(request, "boardinghouse_detail.html", {
        "bh": bh,
        "form": form,
        "booking_status": booking_status,
    })
 

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.profile.is_owner:
                if user.profile.is_approved:
                    login(request, user)
                    return redirect('owner_dashboard')
                else:
                    # Not approved
                    return render(request, 'pendingwait.html')
            else:
                # Not an owner
                login(request, user)
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@login_required
def manual_booking(request, bh_id):
    boardinghouse = get_object_or_404(BoardingHouse, id=bh_id, owner=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        contact_number = request.POST.get('contact_number')

        # ✅ Create approved booking manually
        Booking.objects.create(
            boardinghouse=boardinghouse,
            name=name,
            address=address,
            contact_number=contact_number,
            status='approved',
            created_at=timezone.now()
        )

        # ✅ Reject all other pending bookings for this boarding house
        Booking.objects.filter(
            boardinghouse=boardinghouse,
            status='pending'
        ).update(status='rejected')

        messages.success(request, "Manual booking confirmed successfully.")
        return redirect('owner_dashboard')

@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, boardinghouse__owner=request.user)
    boardinghouse = booking.boardinghouse  # The associated BoardingHouse

    # Check if boardinghouse is full
    if boardinghouse.current_bookings >= boardinghouse.capacity:
        messages.error(request, f"Boarding house {boardinghouse.name} is already full.")
        return redirect('owner_dashboard')

    # Approve the booking
    booking.status = "approved"
    booking.save()

    # Reject other pending bookings only if bedspacer is full (optional logic)
    if boardinghouse.current_bookings >= boardinghouse.capacity:
        Booking.objects.filter(
            boardinghouse=boardinghouse,
            status="pending"
        ).exclude(id=booking.id).update(status="rejected")

    # Send email notification to booker
    if booking.email:  # Make sure Booking model has 'email' field
        visit_date_text = f"\nVisit Date: {booking.visit_date.strftime('%B %d, %Y')}" if booking.visit_date else ""
        send_mail(
            subject=f"Booking Approved: {boardinghouse.name}",
            message=(
                f"Hi {booking.name},\n\n"
                f"Your booking for {boardinghouse.name} has been approved!{visit_date_text}\n\n"
                "Thank you,\nBoardingEase"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[booking.email],
        )

    messages.success(request, "Booking approved successfully and booker notified.")
    return redirect('owner_dashboard')

@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, boardinghouse__owner=request.user)
    boarding_house = booking.boardinghouse

    # Mark booking as rejected
    booking.status = 'rejected'
    booking.save()

    # Remove BH ID from guest session if exists
    bh_id = str(boarding_house.id)
    booked_bhs = request.session.get('booked_boardinghouses', [])
    if bh_id in booked_bhs:
        booked_bhs.remove(bh_id)
        request.session['booked_boardinghouses'] = booked_bhs

    # Check if the boarding house has any approved bookings
    has_approved = boarding_house.bookings.filter(status='approved').exists()

    # If no approved bookings remain, mark the boarding house as not booked
    if not has_approved:
        boarding_house.is_booked = False
        boarding_house.save()

    # Send email notification to booker
    if booking.email:  # Make sure Booking model has 'email' field
        visit_date_text = f"\nVisit Date: {booking.visit_date.strftime('%B %d, %Y')}" if getattr(booking, 'visit_date', None) else ""
        send_mail(
            subject=f"Booking Rejected: {boarding_house.name}",
            message=(
                f"Hi {booking.name},\n\n"
                f"Unfortunately, your booking for {boarding_house.name} has been rejected.{visit_date_text}\n\n"
                "Thank you,\nBoardingEase"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[booking.email],
        )

    messages.info(request, "Booking rejected and booker notified.")
    return redirect('owner_dashboard')

def book_room(request, pk):
    bh = BoardingHouse.objects.get(pk=pk)

    # booking logic...
    messages.success(request, "Booking request submitted successfully!")

    return redirect("boardinghouse_detail", pk=bh.pk)  # ✅ redirect back to details

@login_required
def tenants_view(request, house_id):
    boardinghouse = get_object_or_404(BoardingHouse, id=house_id)

    # Ensure only the owner can access
    if boardinghouse.owner != request.user:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('owner_dashboard')

    # Only bedspacers can access
    if not boardinghouse.is_bedspacer:
        messages.error(request, "Tenant management is only available for bedspacers.")
        return redirect('owner_dashboard')

    tenants = Booking.objects.filter(boardinghouse=boardinghouse, status='approved')

    # Calculate remaining slots
    remaining_slots = boardinghouse.capacity - tenants.count()

    return render(request, 'tenants.html', {
        'boardinghouse': boardinghouse,
        'tenants': tenants,
        'remaining_slots': remaining_slots
    })

def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.status != "pending":
        messages.warning(request, "You can only edit pending bookings.")
        return redirect("home")

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, "Your booking has been updated successfully.")
            return redirect("home")
    else:
        form = BookingForm(instance=booking)

    return render(request, "edit_booking.html", {"form": form, "booking": booking})
