# documents/models.py

from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """
    Stores metadata about uploaded PDFs.
    The actual vector chunks live in Pinecone — this table is the relational record.

    Metadata fields (process, stage, doc_type) mirror what gets stored
    in Pinecone metadata so filtered retrieval works correctly.
    """

    # Process tag — maps to Pinecone metadata filter key "process"
    PROCESS_CHOICES = [
        ('lithography', 'Lithography'),
        ('etching', 'Etching'),
        ('deposition', 'Deposition'),
        ('cmp', 'CMP'),
        ('implantation', 'Ion Implantation'),
        ('diffusion', 'Diffusion'),
        ('metallization', 'Metallization'),
        ('inspection', 'Inspection & Metrology'),
        ('general', 'General'),
    ]

    # Fab stage — maps to Pinecone metadata filter key "stage"
    STAGE_CHOICES = [
        ('FEOL', 'Front End of Line (FEOL)'),
        ('BEOL', 'Back End of Line (BEOL)'),
        ('general', 'General'),
    ]

    DOC_TYPE_CHOICES = [
        ('sop', 'SOP / Process Recipe'),
        ('research_paper', 'Research Paper'),
        ('equipment_spec', 'Equipment Specification'),
        ('defect_library', 'Defect Library'),
        ('training', 'Training Material'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='docs/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Metadata fields — stored here AND passed to Pinecone at ingestion
    process = models.CharField(max_length=50, choices=PROCESS_CHOICES, default='general')
    stage = models.CharField(max_length=10, choices=STAGE_CHOICES, default='general')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='other')
    description = models.TextField(blank=True, default='')

    # Track indexing status
    is_indexed = models.BooleanField(default=False)
    indexing_error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.process} / {self.stage})"

