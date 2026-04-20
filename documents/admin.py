# documents/admin.py

# ============================================================
# DOCUMENT INGESTION PIPELINE TRIGGERED FROM DJANGO ADMIN
#
# Flow implemented here:
#   Admin uploads PDF via Django Admin UI
#          ↓
#   DocumentAdmin.save_model() is called by Django
#          ↓
#   Document record saved to PostgreSQL (title, file, metadata)
#          ↓
#   ingest_document_safe(document) is called automatically
#          ↓
#   Text extracted from PDF (pypdf)
#          ↓
#   Text chunked (SentenceSplitter: 600 tokens, 100 overlap)
#          ↓
#   Chunks embedded (HuggingFace bge-base, runs locally)
#          ↓
#   Embeddings + metadata stored in Pinecone
#          ↓
#   Document.is_indexed = True saved back to PostgreSQL
#
# The admin also shows indexing status, allows re-indexing,
# and displays any ingestion errors directly in the UI.
# ============================================================

from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import path
 
from .models import Document
from .services import ingest_document_safe

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
 
    # --- List view columns ---
    list_display = (
        'id', 'title', 'process', 'stage', 'doc_type',
        'uploaded_by', 'uploaded_at', 'indexing_status_badge'
    )
    list_filter = ('process', 'stage', 'doc_type', 'is_indexed')
    search_fields = ('title', 'description')
 
    # --- Detail view layout ---
    # Fields the admin fills in when uploading a new document
    fieldsets = (
        ('Document File', {
            'fields': ('title', 'file', 'description'),
            'description': 'Upload a PDF file. Text extraction and Pinecone indexing happen automatically on save.'
        }),
        ('Metadata (used for filtered retrieval in Pinecone)', {
            'fields': ('process', 'stage', 'doc_type'),
            'description': (
                'These fields are stored in every Pinecone chunk as metadata. '
                'Engineers can filter queries by process (e.g. etching) or stage (e.g. FEOL).'
            )
        }),
        ('Indexing Status (read-only)', {
            'fields': ('is_indexed', 'indexing_error', 'uploaded_at'),
            'classes': ('collapse',),
        }),
    )
 
    # These are set by the system, not the admin user
    readonly_fields = ('uploaded_at', 'is_indexed', 'indexing_error')
 
    # Show a custom action to re-index selected documents
    actions = ['reindex_documents']
 
    # ----------------------------------------------------------------
    # CORE: Override save_model to trigger ingestion pipeline on upload
    # ----------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        """
        Called by Django Admin whenever a Document is saved (created or edited).
 
        On CREATE (change=False): saves the Document then immediately runs
        the full ingestion pipeline — extract → chunk → embed → Pinecone → PostgreSQL.
 
        On EDIT (change=True): only re-indexes if the file itself was changed.
        This avoids re-indexing on every metadata edit (e.g. changing description).
        """
        # Attach the currently logged-in admin user as uploader
        if not obj.pk:  # new object
            obj.uploaded_by = request.user
 
        # Save the Document record to PostgreSQL first
        # (this writes the file to MEDIA_ROOT via Django FileField)
        super().save_model(request, obj, form, change)
 
        # Decide whether to run ingestion
        file_changed = 'file' in form.changed_data
        is_new = not change
 
        if is_new or file_changed:
            try:
                result_message = ingest_document_safe(obj)
                self.message_user(
                    request,
                    f"✅ {result_message}",
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Ingestion failed for '{obj.title}': {e}",
                    level=messages.ERROR
                )
        else:
            # Metadata-only edit — just confirm save
            self.message_user(
                request,
                f"Document '{obj.title}' metadata updated. File not re-indexed (file unchanged).",
                level=messages.INFO
            )
 
    # ----------------------------------------------------------------
    # Custom column: coloured indexing status badge in list view
    # ----------------------------------------------------------------
    @admin.display(description='Indexed')
    def indexing_status_badge(self, obj):
        if obj.is_indexed:
            return format_html(
                '<span style="color: white; background: #28a745; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">✓ Indexed</span>'
            )
        elif obj.indexing_error:
            return format_html(
                '<span style="color: white; background: #dc3545; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;" title="{}">✗ Error</span>',
                obj.indexing_error[:100]
            )
        else:
            return format_html(
                '<span style="color: white; background: #ffc107; padding: 2px 8px; '
                'border-radius: 4px; font-size: 11px;">⏳ Pending</span>'
            )
 
    # ----------------------------------------------------------------
    # Bulk action: re-index selected documents
    # Useful if Pinecone was wiped or index was recreated
    # ----------------------------------------------------------------
    @admin.action(description='Re-index selected documents in Pinecone')
    def reindex_documents(self, request, queryset):
        success_count = 0
        error_count = 0
 
        for document in queryset:
            try:
                # Reset status before re-indexing
                document.is_indexed = False
                document.indexing_error = ''
                document.save(update_fields=['is_indexed', 'indexing_error'])
 
                ingest_document_safe(document)
                success_count += 1
            except Exception as e:
                error_count += 1
 
        if success_count:
            self.message_user(
                request,
                f"✅ Successfully re-indexed {success_count} document(s).",
                level=messages.SUCCESS
            )
        if error_count:
            self.message_user(
                request,
                f"❌ {error_count} document(s) failed re-indexing. Check 'indexing_error' field.",
                level=messages.ERROR
            )

