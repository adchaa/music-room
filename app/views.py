from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import SignUpForm
from .models import MusicRoom, RoomParticipant
from django.db.models import Count, F
import random
from channels.layers import get_channel_layer


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('/') 
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def home(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'auth/signup.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')


@login_required
def create_or_join_room(request):
    """
    View to create a new room or join an existing room
    """
    available_rooms = MusicRoom.objects.annotate(
        participant_count=Count('participants')
    ).filter(
        is_active=True, 
        participant_count__lt=F('max_participants')
    )

    if available_rooms.exists():
        # Join a random available room
        room = random.choice(list(available_rooms))
    else:
        # Create a new room if no available rooms
        room = MusicRoom.objects.create(
            name=f"Room-{random.randint(1000, 9999)}",
            host=request.user
        )

    # Add current user to the room
    RoomParticipant.objects.create(
        user=request.user, 
        room=room, 
        is_host=room.host == request.user
    )

    return redirect('music_room_detail', room_id=room.id)


@login_required
def music_room_detail(request, room_id):
    try:
        room = MusicRoom.objects.get(id=room_id)
    except MusicRoom.DoesNotExist:
        # If the room doesn't exist, redirect to the home page
        return redirect('home')
    
    participants = room.participants.all()

    context = {
        'room': room,
        'participants': participants,
        'is_host': room.host == request.user
    }

    return render(request, 'music_room.html', context)

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(MusicRoom, id=room_id)

    # Ensure only the host can delete the room
    if room.host == request.user:
        # Notify all participants via WebSocket before deletion
        participants = room.participants.all()
        channel_layer = get_channel_layer()
        # Send the delete notification to all participants
        for participant in participants:
            channel_layer.send(
                participant.user.username,  # Using the username as the channel name
                {
                    'type': 'room_deleted',
                    'message': 'The room has been deleted.',
                }
            )
        
        room.delete()
        messages.success(request, 'Room deleted successfully.')
    else:
        messages.error(request, 'You are not the host of this room.')

    return redirect('home')


@login_required
def skip_room(request, room_id):
    """
    Skip the current room and join another available room.
    """
    current_room = MusicRoom.objects.get(id=room_id)

    # Remove user from the current room
    RoomParticipant.objects.filter(user=request.user, room=current_room).delete()

    # Find another available room
    available_rooms = MusicRoom.objects.annotate(
        participant_count=Count('participants')
    ).filter(
        is_active=True,
        participant_count__lt=F('max_participants')
    ).exclude(id=current_room.id)

    if available_rooms.exists():
        # Join the first available room
        next_room = available_rooms.first()
        RoomParticipant.objects.create(
            user=request.user,
            room=next_room,
            is_host=False
        )
        return redirect('music_room_detail', room_id=next_room.id)

    # If no rooms are available, redirect to the homepage with a message
    messages.warning(request, 'No other music rooms are available. Redirecting to the homepage.')
    return redirect('home')
