import uuid

from django.db import models
from django.contrib.postgres.fields import ArrayField

from sortedm2m.fields import SortedManyToManyField

from cases.enums import CaseType
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    restricted_to = ArrayField(
        base_field=models.TextField(choices=CaseType.choices),
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
