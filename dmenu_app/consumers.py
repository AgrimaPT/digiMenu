# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# class OrderConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         """
#         Establish a WebSocket connection and join appropriate WebSocket groups.
#         """
#         self.table_id = self.scope['url_route']['kwargs'].get('table_id')

#         # Define WebSocket groups
#         self.room_group_name = f'order_{self.table_id}' if self.table_id else 'orders_dashboard'

#         # Join both table-specific and global dashboard groups
#         await self.channel_layer.group_add('orders_dashboard', self.channel_name)
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)

#         await self.accept()

#     async def disconnect(self, close_code):
#         """
#         Disconnect from WebSocket groups.
#         """
#         await self.channel_layer.group_discard('orders_dashboard', self.channel_name)
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         """
#         Handle incoming WebSocket messages and distribute to appropriate groups.
#         """
#         try:
#             text_data_json = json.loads(text_data)
#             order_data = text_data_json.get('order')
#             completed_order_data = text_data_json.get('order_completed')

#             if order_data:
#                 # Broadcast order data to both table-specific and dashboard groups
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {'type': 'order_message', 'order': order_data}
#                 )
#                 await self.channel_layer.group_send(
#                     'orders_dashboard',
#                     {'type': 'order_message', 'order': order_data}
#                 )

#             elif completed_order_data:
#                 # Broadcast completed order updates to groups
#                 await self.channel_layer.group_send(
#                     self.room_group_name,
#                     {'type': 'order_completed', 'completed_order': completed_order_data}
#                 )
#                 await self.channel_layer.group_send(
#                     'orders_dashboard',
#                     {'type': 'order_completed', 'completed_order': completed_order_data}
#                 )

#             else:
#                 await self.send(text_data=json.dumps({'error': 'Invalid data format'}))

#         except json.JSONDecodeError:
#             await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))

#     async def order_message(self, event):
#         """
#         Handle new order messages and send them to the WebSocket client.
#         """
#         order_data = event['order']
#         await self.send(text_data=json.dumps({'order': order_data}))

#     async def order_completed(self, event):
#         """
#         Handle order completion messages and send them to the WebSocket client.
#         """
#         completed_order_data = event['completed_order']
#         await self.send(text_data=json.dumps({'order_completed': completed_order_data}))

#     @staticmethod
#     def send_order_update(table_id, order_data):
#         """
#         Function to send new order updates.
#         """
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f'order_{table_id}',
#             {'type': 'order_message', 'order': order_data}
#         )
#         async_to_sync(channel_layer.group_send)(
#             'orders_dashboard',
#             {'type': 'order_message', 'order': order_data}
#         )

#     @staticmethod
#     def send_order_completed_update(table_id, completed_order_data):
#         """
#         Function to send completed order updates.
#         """
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             f'order_{table_id}',
#             {'type': 'order_completed', 'completed_order': completed_order_data}
#         )
#         async_to_sync(channel_layer.group_send)(
#             'orders_dashboard',
#             {'type': 'order_completed', 'completed_order': completed_order_data}
#         )



import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Determine room name dynamically based on table ID or a default group
        self.room_name = self.scope['url_route']['kwargs'].get('table_id', 'orders_dashboard')
        self.room_group_name = f'order_{self.room_name}'

        # Join the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )


        await self.accept()
       
    async def disconnect(self, close_code):
        # Leave the WebSocket group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            # Parse the incoming WebSocket message
            text_data_json = json.loads(text_data)
            order_data = text_data_json.get('order')

            if not order_data:

                await self.send(text_data=json.dumps({'error': 'Invalid order data'}))
                return

            # Broadcast the order data to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'order_message',
                    'order': order_data
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))

    # Handle broadcasted messages of type 'order_message'
    async def order_message(self, event):
        order_data = event['order']

        # Send the order data back to the WebSocket client
        await self.send(text_data=json.dumps({
            'order': order_data
        }))

    # Handle broadcasted messages of type 'order_completed'
    async def order_completed(self, event):
        # Send the data about completed order updates back to the WebSocket client
        await self.send(text_data=json.dumps(event))

    # This method sends updates when a new order is placed or completed
    def send_order_update(self, order_data):
        channel_layer = get_channel_layer()

        # Broadcast the order update to the group (room)
        async_to_sync(channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'order_message',  # Type for broadcasting the new order data
                'order': order_data
            }
        )

    def send_order_completed_update(self, completed_order_data):
        channel_layer = get_channel_layer()

        # Broadcast the completed order update to the group (room)
        async_to_sync(channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'order_completed',  # Type for broadcasting completed order
                'completed_order': completed_order_data
            }
        )

