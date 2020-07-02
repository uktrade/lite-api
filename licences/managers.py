from django.db import models

from licences.enums import LicenceStatus


class LicenceManager(models.Manager):
    def get_active_licence(self, application):
        return self.get(
            application=application, status__in=[LicenceStatus.ISSUED.value, LicenceStatus.REINSTATED.value]
        )

    def get_draft_licence(self, application):
        return self.get(
            application=application, status=LicenceStatus.DRAFT.value
        )

    def get_draft_or_active_licence(self, application):
        """
        Returns the Licence to be considered during finalised flow.
        Prioritise getting draft licences, followed by active licences.
        """
        try:
            return self.get_draft_licence(application)
        except self.DoesNotExist:
            try:
                return self.get_active_licence(application)
            except self.DoesNotExist:
                return None
