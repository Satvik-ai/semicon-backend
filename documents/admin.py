# documents/admin.py

from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'process', 'stage', 'doc_type', 'uploaded_by', 'uploaded_at', 'is_indexed')
    list_filter = ('process', 'stage', 'doc_type', 'is_indexed')
    search_fields = ('title', 'description')
    readonly_fields = ('uploaded_at', 'is_indexed', 'indexing_error')

