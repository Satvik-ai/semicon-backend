#semicon_chatbot_backend/urls.py
"""
URL configuration for semicon_chatbot_backend project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chat/', include('chat.urls')),
    path('api/upload/', include('documents.urls')),
]

