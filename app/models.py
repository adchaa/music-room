from django.db import models
from django.contrib.auth.models import User

class MusicRoom(models.Model):
    """
    Model representing a music room
    """
    name = models.CharField(max_length=100, unique=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    current_track = models.CharField(max_length=200, null=True, blank=True)
    max_participants = models.IntegerField(default=10)

class RoomParticipant(models.Model):
    """
    Model to track room participants
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(MusicRoom, on_delete=models.CASCADE, related_name='participants')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_host = models.BooleanField(default=False)
