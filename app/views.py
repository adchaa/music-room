from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.contrib import messages
from .forms import SignUpForm
from .models import MusicRoom,RoomParticipant
from django.db.models import Count,F
import random

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
def create_room(request):
    room = MusicRoom.objects.create(
        name=f"Room-{random.randint(1000, 9999)}",
        host=request.user
    )

    return redirect('music_room_detail', room_id=room.id)

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
        room = random.choice(list(available_rooms))
    else:
        room = MusicRoom.objects.create(
            name=f"Room-{random.randint(1000, 9999)}",
            host=request.user
        )


    return redirect('music_room_detail', room_id=room.id)

@login_required
def music_room_detail(request, room_id):
    """
    View to display a specific music room
    """
    try:
        room = MusicRoom.objects.get(id=room_id)
    except MusicRoom.DoesNotExist:
        return redirect('home')
    room = MusicRoom.objects.get(id=room_id)
    participants = room.participants.all()
    
    context = {
        'room': room,
        'participants': participants,
        'is_host': room.host == request.user
    }
    return render(request, 'music_room.html', context)

@login_required
def skip_room(request, room_id):
    """
    Skip the current room and join another available room.
    """
    current_room = MusicRoom.objects.get(id=room_id)
    RoomParticipant.objects.filter(user=request.user, room=current_room).delete()
    available_rooms = MusicRoom.objects.annotate(
        participant_count=Count('participants')
    ).filter(
        is_active=True,
        participant_count__lt=F('max_participants')
    ).exclude(id=current_room.id)
    if available_rooms.exists():
        next_room = random.choice(list(available_rooms))
        return redirect('music_room_detail', room_id=next_room.id)
    messages.warning(request, 'No other music rooms are available. Redirecting to the homepage.')
    return redirect('home')
