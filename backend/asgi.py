"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

"""import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = get_asgi_application()"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.routing import websocket_urlpatterns

#on definit les regles par defaut de django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

#c'est ici l'aiguillage se fait
application = ProtocolTypeRouter({
    # 1️⃣ Pour les requêtes HTTP normales (Django classique)
    "http": get_asgi_application(),
    # 2️⃣ Pour les connexions WebSocket
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
