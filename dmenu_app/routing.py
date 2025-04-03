from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    re_path('ws/orders/', consumers.OrderConsumer.as_asgi()),
    re_path(r'ws/table/(?P<table_id>\d+)/orders/$',consumers.OrderConsumer.as_asgi()),
   
]
