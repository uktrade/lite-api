import uuid

from django.db import models, transaction

from sortedm2m.fields import SortedManyToManyField

from cases.enums import CaseType
from picklists.models import PicklistItem
from static.letter_layouts.models import LetterLayout


class LetterTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=35, unique=True)
    layout = models.ForeignKey(LetterLayout, on_delete=models.CASCADE, null=False)
    letter_paragraphs = SortedManyToManyField(PicklistItem)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def restricted_to(self):
        return TemplateCaseTypes.objects.filter(letter_template=self).values_list("case_type", flat=True)

    @restricted_to.setter
    @transaction.atomic
    def restricted_to(self, case_types: [str]):
        TemplateCaseTypes.objects.filter(letter_template=self).delete()

        for case_type in case_types:
            TemplateCaseTypes.objects.create(letter_template=self, case_type=case_type)


class TemplateCaseTypes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    letter_template = models.ForeignKey(LetterTemplate, on_delete=models.CASCADE, null=False)
    case_type = models.CharField(choices=CaseType.choices, default=CaseType.APPLICATION, max_length=35)
