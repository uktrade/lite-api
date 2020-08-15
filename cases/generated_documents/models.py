from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from cases.enums import AdviceType
from cases.models import CaseDocument
from api.licences.models import Licence
from api.users.models import ExporterNotification
from api.letter_templates.models import LetterTemplate
from api.users.models import UserOrganisationRelationship


class GeneratedCaseDocument(CaseDocument):
    template = models.ForeignKey(LetterTemplate, on_delete=models.DO_NOTHING)
    text = models.TextField(blank=True)

    notifications = GenericRelation(ExporterNotification, related_query_name="generated_case_document",)
    advice_type = models.CharField(choices=AdviceType.choices, max_length=30, null=True, blank=False)
    licence = models.ForeignKey(Licence, null=True, on_delete=models.DO_NOTHING)

    def send_exporter_notifications(self):
        for user_relationship in UserOrganisationRelationship.objects.filter(organisation=self.case.organisation):
            user_relationship.send_notification(content_object=self, case=self.case)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super(GeneratedCaseDocument, self).save(*args, **kwargs)

        if creating and self.visible_to_exporter:
            self.send_exporter_notifications()

    class Meta:
        ordering = ["name"]
