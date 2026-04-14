# chat/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import query_chatbot
from .models import ChatSession, ChatMessage, Feedback


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_view(request):
    """
    POST /api/chat/
    Body: { "query": "...", "session_id": (optional), "process": (optional), "stage": (optional) }
    """
    query = request.data.get("query", "").strip()

    if not query:
        return Response(
            {"error": "Field 'query' is required and cannot be empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    session_id = request.data.get("session_id")
    process_filter = request.data.get("process")   # e.g. "etching"
    stage_filter = request.data.get("stage")       # e.g. "FEOL"

    result = query_chatbot(
        user=request.user,
        user_query=query,
        session_id=session_id,
        process_filter=process_filter,
        stage_filter=stage_filter,
    )

    if "error" in result:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    return Response(result, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history_view(request):
    """
    GET /api/chat/history/
    Returns all sessions for the logged-in user, with messages.
    """
    sessions = ChatSession.objects.filter(user=request.user).prefetch_related('messages')

    data = []
    for session in sessions:
        messages = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "sources": msg.sources,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in session.messages.all()
        ]
        data.append({
            "session_id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "messages": messages,
        })

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def feedback_view(request, message_id):
    """
    POST /api/chat/feedback/<message_id>/
    Body: { "vote": "up" | "down", "comment": "(optional)" }

    Allows engineers to rate assistant responses — critical for eval pipeline.
    """
    try:
        message = ChatMessage.objects.get(id=message_id, session__user=request.user, role='assistant')
    except ChatMessage.DoesNotExist:
        return Response({"error": "Message not found."}, status=status.HTTP_404_NOT_FOUND)

    vote = request.data.get("vote")
    if vote not in ('up', 'down'):
        return Response({"error": "Vote must be 'up' or 'down'."}, status=status.HTTP_400_BAD_REQUEST)

    feedback, created = Feedback.objects.update_or_create(
        message=message,
        defaults={
            "vote": vote,
            "comment": request.data.get("comment", "")
        }
    )

    return Response({
        "message_id": message_id,
        "vote": feedback.vote,
        "created": created
    }, status=status.HTTP_200_OK)