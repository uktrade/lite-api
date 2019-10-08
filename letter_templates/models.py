import uuid

from django.core.exceptions import ValidationError
from django.db import models

from cases.enums import CaseType
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = models.ManyToManyField(PicklistItem)
    restricted_to = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.id

    def save(self, *args, **kwargs):
        # Convert restricted_to to list if it isn't already
        self.restricted_to = [self.restricted_to] if isinstance(self.restricted_to, str) else self.restricted_to

        # If restricted_to doesn't match case type choices, raise error
        for item in self.restricted_to:
            if item not in [x[0] for x in CaseType.choices]:
                raise ValidationError('Must be a suitable case type for restricted to')

        self.restricted_to = ','.join(self.restricted_to)

        super(LetterTemplate, self).save(*args, **kwargs)
