from django.apps import AppConfig
from django.db.models.signals import post_migrate

from conf.settings import LITE_HMRC_INTEGRATION_ENABLED


class LicencesConfig(AppConfig):
    name = "licences"

    @classmethod
    def initialize_background_tasks(cls, **kwargs):
        from licences.models import Licence
        from licences.tasks import schedule_licence_for_hmrc_integration

        licences_not_sent = Licence.objects.filter(is_complete=True, sent_at__isnull=True)

        for licence in licences_not_sent:
            schedule_licence_for_hmrc_integration(str(licence.id), licence.application.reference_code)

    def ready(self):
        if LITE_HMRC_INTEGRATION_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
