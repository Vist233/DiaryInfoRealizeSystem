from channels.generic.websocket import AsyncWebsocketConsumer


class NoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"status": "connected"})

    async def receive(self, text_data=None, bytes_data=None):
        # Echo for MVP
        if text_data:
            await self.send(text_data=text_data)

    async def disconnect(self, close_code):
        pass

