# documents/urls.py
from django.urls import path
from .views import upload_document, list_documents

urlpatterns = [
    path('', upload_document, name='upload_document'),
    path('list/', list_documents, name='list_documents'),
]
