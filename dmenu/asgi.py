"""
ASGI config for dmenu project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from dmenu_app.routing import websocket_urlpatterns  # Using routing.py for organization

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmenu.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Import WebSocket URL patterns from routing.py
        )
    ),
})
