import os

import django

# Setup Django ASGI application.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "waveview.settings")
django.setup()

# Import ASGI modules.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Get the Django ASGI application.
asgi_app = get_asgi_application()

# Import the websocket URL patterns.
from waveview.routing import websocket_urlpatterns
from waveview.websocket.middleware import JWTAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
