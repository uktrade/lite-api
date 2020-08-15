from django.db import models

from api.licences.enums import LicenceStatus


class LicenceManager(models.Manager):
    def get_active_licence(self, application):
        return self.get(case=application, status__in=[LicenceStatus.ISSUED, LicenceStatus.REINSTATED])

    def get_draft_licence(self, application):
        return self.get(case=application, status=LicenceStatus.DRAFT)

    def get_draft_or_active_licence(self, application):
        """
        Returns the Licence to be considered during finalised flow.
        Prioritise getting draft licences, followed by active licences.
        """
        try:
            return self.get_draft_licence(application)
        except self.model.DoesNotExist:
            try:
                return self.get_active_licence(application)
            except self.model.DoesNotExist:
                return None
