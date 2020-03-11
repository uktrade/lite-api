from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from cases.models import CaseDocument
from users.models import ExporterNotification
from letter_templates.models import LetterTemplate
from users.models import UserOrganisationRelationship


class GeneratedCaseDocument(CaseDocument):
    template = models.ForeignKey(LetterTemplate, on_delete=models.DO_NOTHING)
    text = models.TextField(blank=True)

    notifications = GenericRelation(ExporterNotification, related_query_name="generated_case_document",)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super(GeneratedCaseDocument, self).save(*args, **kwargs)

        if creating:
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=self.case.organisation):
                user_relationship.send_notification(content_object=self, case=self.case)

    class Meta:
        ordering = ["name"]
