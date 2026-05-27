# chat/management/commands/setup_admin.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from semicon_chatbot_backend.settings import ADMIN_USERNAME, ADMIN_PASSWORD


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        username = ADMIN_USERNAME
        password = ADMIN_PASSWORD

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email='admin@semiconchat.com',
                password=password
            )
            self.stdout.write(f'Superuser created: {username}')
        else:
            user = User.objects.get(username=username)
            self.stdout.write(f'Superuser already exists: {username}')

        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write(f'AUTH TOKEN: {token.key}')

