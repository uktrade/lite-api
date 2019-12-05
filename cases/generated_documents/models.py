from django.db import models

from cases.models import CaseDocument
from letter_templates.models import LetterTemplate
from users.models import UserOrganisationRelationship


class GeneratedCaseDocument(CaseDocument):
    template = models.ForeignKey(LetterTemplate, on_delete=models.DO_NOTHING)

    def save(self, *args, **kwargs):
        creating = self._state.adding is True
        super(GeneratedCaseDocument, self).save(*args, **kwargs)

        if creating:
            for user_relationship in UserOrganisationRelationship.objects.filter(organisation=self.case.organisation):
                user_relationship.user.send_notification(generated_case_document=self)
