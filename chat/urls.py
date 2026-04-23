# chat/urls.py
from django.urls import path
from .views import chat_view, history_view, feedback_view, upload_excel_view, create_session_view

urlpatterns = [
    path('', chat_view, name='chat'),
    path('history/', history_view, name='chat-history'),
    path('feedback/<int:message_id>/', feedback_view, name='chat-feedback'),
    path('upload-excel/', upload_excel_view, name='upload-excel'),
    path('create-session/',     create_session_view,  name='create-session'),
]
