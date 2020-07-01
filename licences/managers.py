from django.db import models, transaction

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
