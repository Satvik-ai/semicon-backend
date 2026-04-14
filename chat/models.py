# chat/models.py

from django.db import models
from django.contrib.auth.models import User

class ChatSession(models.Model):
    """
    Groups messages into a conversation session per user.
    Useful for the /history endpoint and session-based UI.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.id} — {self.user.username} ({self.created_at.date()})"

class ChatMessage(models.Model):
    """
    Stores each query-response pair with sources.
    Sources are stored as JSON (list of source text chunks or doc references).
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()

    # Stores retrieved source references as JSON list
    # e.g. [{"text": "...", "doc_title": "TSMC 5nm SOP", "page": 3}]
    sources = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] Session {self.session_id} — {self.content[:60]}"

class Feedback(models.Model):
    """
    Thumbs up / down feedback on assistant responses.
    Linked to the specific assistant message.
    """
    THUMBS_UP = 'up'
    THUMBS_DOWN = 'down'
    VOTE_CHOICES = [(THUMBS_UP, 'Up'), (THUMBS_DOWN, 'Down')]

    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='feedback',
        limit_choices_to={'role': 'assistant'}
    )
    vote = models.CharField(max_length=4, choices=VOTE_CHOICES)
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vote} — Message {self.message_id}"

