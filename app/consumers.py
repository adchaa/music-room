import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class MusicRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'music_room_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'play_track':
            # Broadcast track to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'play_track',
                    'track': data.get('track'),
                    'user': self.scope['user'].username
                }
            )

    # Handlers for different message types
    async def play_track(self, event):
        # Send track to WebSocket
        await self.send(text_data=json.dumps({
            'action': 'play_track',
            'track': event['track'],
            'user': event['user']
        }))