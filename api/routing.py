from django.urls import re_path
from . import consumers

#cette liste definit les urls pour les websockets
websocket_urlpatterns = [
    # re_path fonctionne comme path() mais accepte les expressions regulieres
    #l'URL sera: ws://mon-serveur/ws/eleves/
    # L'URL sera : ws://127.0.0.1:8000/ws/eleves/
    # re_path(r'ws/eleves/$', consumers.EleveConsumer.as_asgi()),
    re_path("ws/etablissement/(?P<etab_id>[0-9a-f-]+)/$", consumers.EtablissementConsumer.as_asgi()),
]