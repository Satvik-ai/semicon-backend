# chat/urls.py
from django.urls import path
from .views import chat_view, history_view, feedback_view

urlpatterns = [
    path('', chat_view, name='chat'),
    path('history/', history_view, name='chat-history'),
    path('feedback/<int:message_id>/', feedback_view, name='chat-feedback'),
]
