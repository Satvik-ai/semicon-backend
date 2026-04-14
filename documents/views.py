# documents/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import ingest_document

@api_view(['POST'])
def upload_document(request):
    file = request.FILES['file']

    file_path = f"media/{file.name}"

    with open(file_path, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)

    ingest_document(file_path)

    return Response({"status": "uploaded"})
