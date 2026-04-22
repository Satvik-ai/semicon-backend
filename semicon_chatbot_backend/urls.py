#semicon_chatbot_backend/urls.py
"""
URL configuration for semicon_chatbot_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth — token login/logout via DRF
    path('api/auth/', include('rest_framework.urls')),
    path('api/auth/login/', obtain_auth_token, name='api-token-auth'),

    # App routes
    path('api/chat/', include('chat.urls')),
    path('api/upload/', include('documents.urls')),
]

# Serve media files in development (Django handles this; use nginx/S3 in production)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

