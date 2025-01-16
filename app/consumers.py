import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import MusicRoom,RoomParticipant
from channels.db import database_sync_to_async

class MusicRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'music_room_{self.room_id}'
            self.user = self.scope["user"]

            room = await database_sync_to_async(MusicRoom.objects.get)(id=self.room_id)
            existing_participant = await database_sync_to_async(
             RoomParticipant.objects.filter(
                user=self.user,
                room__id=self.room_id
            ).exists)()
            

    

            if not existing_participant:
                await database_sync_to_async(lambda :RoomParticipant.objects.create(
                    user=self.user,
                    room=room,
                    is_host=room.host == self.user
                ))()

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()

            if room.current_track:
                await self.send(text_data=json.dumps({
                    'action': 'play_track',
                    'track': room.current_track,
                    'user': room.host.username
                }))

        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()


    async def disconnect(self, close_code):
        try:
            await database_sync_to_async(RoomParticipant.objects.filter(
                user=self.user,
                room__id=self.room_id
            ).delete)()
            

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'play_track':
            await self.update_current_track(data['room_id'], data['track'], self.scope['user'].username)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'play_track',
                    'track': data.get('track'),
                    'user': self.scope['user'].username
                }
            )

    @database_sync_to_async
    def update_current_track(self, room_id, track, user):
        room = MusicRoom.objects.get(id=room_id)
        room.current_track = track
        room.save()

    async def play_track(self, event):
        await self.send(text_data=json.dumps({
            'action': 'play_track',
            'track': event['track'],
            'user': event['user']
        }))