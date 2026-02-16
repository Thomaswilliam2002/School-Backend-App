from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from api.models import Staff

User = get_user_model()

@database_sync_to_async
def get_user(token_key):
    try:
        # On décode le token JWT
        access_token = AccessToken(token_key)
        print(access_token)
        # On récupère l'utilisateur via l'ID contenu dans le token
        # print(access_token['user_id'])
        staff = Staff.objects.select_related('user').get(user__id=access_token['user_id'])
        print(staff)
        return staff
    except Exception:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # On cherche le paramètre "token" dans l'URL (query_string)
        query_dict = dict(e.split('=') for e in scope['query_string'].decode().split('&') if '=' in e)
        token_key = query_dict.get('token')

        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)