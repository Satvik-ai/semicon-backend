#semicon_chatbot_backend/asgi.py
"""
ASGI config for semicon_chatbot_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'semicon_chatbot_backend.settings')

application = get_asgi_application()
