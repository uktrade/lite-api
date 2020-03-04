import uuid

from django.db import models
from separatedvaluesfield.models import SeparatedValuesField

from sortedm2m.fields import SortedManyToManyField

from cases.models import CaseType
from common.models import TimestampableModel
from static.decisions.enums import Decisions
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35, unique=True)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    case_types = models.ManyToManyField(CaseType, related_name="letter_templates")
    decisions = SeparatedValuesField(max_length=150, choices=Decisions.choices, blank=True, null=True, default=None)

    class Meta:
        ordering = ["name"]
