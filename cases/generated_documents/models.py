from django.db import models

from cases.models import CaseDocument
from letter_templates.models import LetterTemplate


class GeneratedCaseDocument(CaseDocument):
    template = models.ForeignKey(LetterTemplate, on_delete=models.DO_NOTHING)
