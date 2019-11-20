import uuid

from django.db import models

from cases.models import Case, CaseDocument
from documents.models import Document
from letter_templates.models import LetterTemplate


class GeneratedDocument(CaseDocument):
    template = models.ForeignKey(LetterTemplate, on_delete=models.DO_NOTHING)
