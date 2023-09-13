from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.conf import settings

from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action


class LicencesConfig(AppConfig):
    name = "api.licences"

    def initialize_background_tasks(self, **kwargs):
        if settings.LITE_HMRC_INTEGRATION_ENABLED:
            self.schedule_not_sent_licences()

    @staticmethod
    def schedule_not_sent_licences():
        """Send licence info to HMRC integration"""

        from api.licences.models import Licence
        from api.licences.tasks import schedule_licence_for_hmrc_integration

        licences_not_sent = Licence.objects.filter(hmrc_integration_sent_at__isnull=True).exclude(
            status=LicenceStatus.DRAFT
        )

        for licence in licences_not_sent:
            schedule_licence_for_hmrc_integration(
                str(licence.id), licence_status_to_hmrc_integration_action.get(licence.status)
            )

    def ready(self):
        if settings.BACKGROUND_TASK_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
