import uuid

from django.db import models

from sortedm2m.fields import SortedManyToManyField

from cases.models import CaseType
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35, unique=True)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    case_types = models.ManyToManyField(CaseType, related_name="letter_templates")

    class Meta:
        ordering = ["name"]
