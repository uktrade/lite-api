import uuid

from django.db import models

from sortedm2m.fields import SortedManyToManyField

from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    restricted_to = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return str(self.id)
