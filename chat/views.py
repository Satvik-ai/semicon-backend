# chat/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import query_chatbot

@api_view(['POST'])
def chat_view(request):
    query = request.data.get("query")

    result = query_chatbot(query)

    return Response(result)
