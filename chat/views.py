# chat/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import query_chatbot
from .models import ChatSession, ChatMessage, Feedback, ExcelContext

import pandas as pd
import io


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_excel_view(request):
    """
    POST /api/chat/upload-excel/
    Multipart form: { "file": <xlsx file>, "session_id": <int> }

    Parses the uploaded Excel file into a markdown table and stores
    it in ExcelContext scoped to the given session. Subsequent queries
    on that session will have this table injected into the LLM prompt.
    """
    if 'file' not in request.FILES:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    file   = request.FILES['file']
    session_id = request.data.get('session_id')

    if not file.name.endswith(('.xlsx', '.xls')):
        return Response({"error": "Only .xlsx and .xls files are supported."}, status=status.HTTP_400_BAD_REQUEST)

    if not session_id:
        return Response({"error": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = ChatSession.objects.get(id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        file_bytes = io.BytesIO(file.read())

        # sheet_name=None → returns a dict: { "Sheet1": df1, "Sheet2": df2, ... }
        all_sheets = pd.read_excel(file_bytes, sheet_name=None)

        sheet_sections = []
        total_rows = 0

        for sheet_name, df in all_sheets.items():

            # Skip completely empty sheets
            if df.empty:
                continue

            # Cap each sheet at 500 rows to avoid token overflow
            if len(df) > 500:
                df = df.head(500)

            total_rows += len(df)

            # Each sheet is labelled clearly so the LLM knows which sheet data came from
            sheet_sections.append(
                f"### Sheet: {sheet_name}\n"
                f"Rows: {len(df)} | Columns: {', '.join(str(c) for c in df.columns)}\n\n"
                f"{df.to_markdown(index=False)}"
            )

        if not sheet_sections:
            return Response({"error": "Excel file has no data."}, status=status.HTTP_400_BAD_REQUEST)

        # Join all sheets into one text block separated by dividers
        table_text = "\n\n---\n\n".join(sheet_sections)
    except Exception as e:
        return Response({"error": f"Failed to parse Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    # Store/replace excel context for this session
    ExcelContext.objects.update_or_create(
        session=session,
        defaults={
            "filename":   file.name,
            "table_text": table_text,
        }
    )

    return Response({
        "status":     "uploaded",
        "filename":   file.name,
        "sheets":     list(all_sheets.keys()),
        "total_rows": total_rows,
        "session_id": session.id,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session_view(request):
    """
    POST /api/chat/create-session/
    Creates an empty ChatSession and returns its ID.
    Used by the frontend when uploading an Excel file before
    any message has been sent — avoids creating phantom messages.
    """
    session = ChatSession.objects.create(
        user=request.user,
        title=request.data.get('title', 'New Chat')
    )
    return Response({
        "session_id": session.id,
        "title":      session.title,
    }, status=status.HTTP_201_CREATED)

