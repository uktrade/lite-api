import uuid

from django.db import models
from sortedm2m.fields import SortedManyToManyField

from cases.models import CaseType
from api.common.models import TimestampableModel
from api.picklists.models import PicklistItem
from static.decisions.models import Decision
from static.letter_layouts.models import LetterLayout


class LetterTemplate(TimestampableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35, unique=True)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    case_types = models.ManyToManyField(CaseType, related_name="letter_templates")
    decisions = models.ManyToManyField(Decision, related_name="letter_templates")
    visible_to_exporter = models.BooleanField(blank=False, null=False)
    include_digital_signature = models.BooleanField(blank=False, null=False)

    class Meta:
        ordering = ["name"]
