from django.apps import AppConfig
from django.db.models.signals import post_migrate

from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action


class LicencesConfig(AppConfig):
    name = "api.licences"

    def initialize_tasks(self, **kwargs):
        self.schedule_not_sent_licences()

    @staticmethod
    def schedule_not_sent_licences():
        from api.licences.models import Licence
        from api.licences.celery_tasks import schedule_licence_details_to_lite_hmrc

        licences_not_sent = Licence.objects.filter(hmrc_integration_sent_at__isnull=True).exclude(
            status=LicenceStatus.DRAFT
        )

        for licence in licences_not_sent:
            schedule_licence_details_to_lite_hmrc(
                str(licence.id), licence_status_to_hmrc_integration_action.get(licence.status)
            )

    def ready(self):
        post_migrate.connect(self.initialize_tasks, sender=self)
