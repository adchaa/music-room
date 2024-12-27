from django.contrib import admin
from .models import MusicRoom, RoomParticipant

# Simple registration
admin.site.register(MusicRoom)
admin.site.register(RoomParticipant)