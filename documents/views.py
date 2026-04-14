# documents/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from .models import Document
from .services import ingest_document_safe


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def upload_document(request):
    """
    POST /api/upload/
    Admin-only. Accepts a PDF file + metadata fields.

    Body (multipart/form-data):
      - file: <PDF file>
      - title: string
      - process: e.g. "etching"
      - stage: e.g. "FEOL"
      - doc_type: e.g. "sop"
      - description: (optional)
    """
    if 'file' not in request.FILES:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    title = request.data.get('title', file.name)

    if not file.name.endswith('.pdf'):
        return Response({"error": "Only PDF files are supported."}, status=status.HTTP_400_BAD_REQUEST)

    # Save Document record — Django handles the file path via MEDIA_ROOT
    document = Document.objects.create(
        title=title,
        file=file,
        uploaded_by=request.user,
        process=request.data.get('process', 'general'),
        stage=request.data.get('stage', 'general'),
        doc_type=request.data.get('doc_type', 'other'),
        description=request.data.get('description', ''),
    )

    # Run ingestion pipeline
    try:
        message = ingest_document_safe(document)
        return Response({
            "status": "success",
            "message": message,
            "document_id": document.id,
            "title": document.title,
            "is_indexed": document.is_indexed,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "document_id": document.id,
            "error": str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_documents(request):
    """
    GET /api/upload/
    Admin-only. Lists all uploaded documents with indexing status.
    """
    docs = Document.objects.all().values(
        'id', 'title', 'process', 'stage', 'doc_type',
        'uploaded_at', 'is_indexed', 'indexing_error',
        'uploaded_by__username'
    )
    return Response(list(docs))

