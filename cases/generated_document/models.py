import uuid

from django.db import models

from cases.models import Case
from documents.models import Document
from letter_templates.models import LetterTemplate


class GeneratedDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    template = models.ForeignKey(LetterTemplate, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=False, blank=False)

