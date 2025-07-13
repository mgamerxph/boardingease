from django.shortcuts import render, redirect
from .models import BoardingHouse  # import your model
from django.contrib.auth.decorators import login_required
from .models import BoardingHouse, Profile, Booking  # ✅ Add Profile here
from .forms import BoardingHouseForm  # ✅ import your form
from django.contrib.auth.models import User
from .forms import OwnerRegistrationForm, BookingForm
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator

def home(request):
    query = request.GET.get('q')  # Get search input
    booked_bhs = request.session.get('booked_boardinghouses', [])

    # ✅ Filter by address if search query exists
    if query:
        boardinghouses = BoardingHouse.objects.filter(address__icontains=query)
    else:
        boardinghouses = BoardingHouse.objects.all()

    for bh in boardinghouses:
        latest_booking = Booking.objects.filter(
            boardinghouse=bh
        ).order_by('-id').first()

        # ✅ Status logic: booked = approved
        bh.is_booked = latest_booking.status == 'approved' if latest_booking else False

        # ✅ Session-based pending flag logic
        if str(bh.id) in booked_bhs:
            pending_booking = Booking.objects.filter(
                boardinghouse=bh,
                status='pending'
            ).order_by('-id').first()

            bh.is_pending_for_this_user = bool(pending_booking)
            bh.pending_booking_id = pending_booking.id if pending_booking else None
        else:
            bh.is_pending_for_this_user = False
            bh.pending_booking_id = None

    # ✅ Send both results and query back to template
    return render(request, 'home.html', {
        'boardinghouses': boardinghouses,
        'query': query,  # needed to retain input value in form
    })

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

    for bh in boardinghouses:
        bh.approved_booking = Booking.objects.filter(
            boardinghouse=bh,
            status='approved'
        ).first()
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
        all_pending = all_pending.filter(boardinghouse__id=selected_bh)

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
        return redirect('home')  # only owners can add BHs

    if request.method == 'POST':
        # ✅ Add request.FILES to handle image uploads
        form = BoardingHouseForm(request.POST, request.FILES)   
        if form.is_valid():
            bh = form.save(commit=False)
            bh.owner = request.user  # ✅ assign owner
            bh.save()
            messages.success(request, "Boarding house added successfully.")
            return redirect('owner_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BoardingHouseForm()

    return render(request, 'add_boardinghouse.html', {'form': form})

def register_owner(request):
    if request.method == 'POST':
        form = OwnerRegistrationForm(request.POST)
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

    if bh_id_str in session_booked:
        user_booking = Booking.objects.filter(boardinghouse=bh).order_by('-id').first()
        if user_booking:
            booking_status = user_booking.status

            # ✅ If booking is rejected or cancelled, remove from session
            if booking_status in ['rejected', 'cancelled']:
                session_booked.remove(bh_id_str)
                request.session['booked_boardinghouses'] = session_booked
                booking_status = None

    return render(request, 'boardinghouse_detail.html', {
        'bh': bh,
        'booking_status': booking_status,
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

def book_boardinghouse(request, pk):
    bh = get_object_or_404(BoardingHouse, pk=pk)

    # ✅ Check if this user/session already booked this BH
    booked_bhs = request.session.get('booked_boardinghouses', [])
    if str(pk) in booked_bhs:
        messages.warning(request, "You’ve already booked this boarding house. Please wait for approval.")
        return redirect('boardinghouse_detail', pk=pk)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.boardinghouse = bh
            booking.status = 'pending'
            booking.save()

            # ✅ Save in session to prevent repeat booking
            booked_bhs.append(str(pk))
            request.session['booked_boardinghouses'] = booked_bhs

            messages.success(request, "Boarding house booked successfully. Please wait for approval.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BookingForm()

    return render(request, 'booking_form.html', {
        'form': form,
        'bh': bh
    })

@login_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, boardinghouse__owner=request.user)

    # Approve the selected booking
    booking.status = 'approved'
    booking.save()

    # ✅ Delete all other pending bookings for the same boarding house
    Booking.objects.filter(
        boardinghouse=booking.boardinghouse,
        status='pending'
    ).exclude(id=booking.id).update(status='rejected')
    
    messages.success(request, "Booking approved successfully.")
    return redirect('owner_dashboard')

@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, boardinghouse__owner=request.user)

    # ✅ Mark booking as rejected
    booking.status = 'rejected'
    booking.save()

    # ✅ Remove BH ID from guest session if exists
    bh_id = str(booking.boardinghouse.id)
    booked_bhs = request.session.get('booked_boardinghouses', [])
    if bh_id in booked_bhs:
        booked_bhs.remove(bh_id)
        request.session['booked_boardinghouses'] = booked_bhs

    # ✅ Check if the boarding house has any other approved bookings
    boarding_house = booking.boardinghouse
    has_approved = boarding_house.booking_set.filter(status='approved').exists()

    # ✅ If no approved bookings remain, mark the boarding house as not booked
    if not has_approved:
        boarding_house.is_booked = False
        boarding_house.save()

    messages.info(request, "Booking rejected.")
    return redirect('owner_dashboard')