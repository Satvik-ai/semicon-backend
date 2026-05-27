# chat/management/commands/setup_admin.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from semicon_chatbot_backend.settings import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        if not User.objects.filter(username=ADMIN_USERNAME).exists():
            user = User.objects.create_superuser(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD
            )
            self.stdout.write(f'Superuser created: {ADMIN_USERNAME}')
        else:
            user = User.objects.get(username=ADMIN_USERNAME)
            self.stdout.write(f'Superuser already exists: {ADMIN_USERNAME}')

        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write(f'AUTH TOKEN: {token.key}')

