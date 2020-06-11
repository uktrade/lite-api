from django.apps import AppConfig

from conf.settings import LITE_HMRC_INTEGRATION_ENABLED


class LicencesConfig(AppConfig):
    name = "licences"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from licences.models import Licence
        from licences.tasks import schedule_licence_for_hmrc_integration

        licences_not_sent = Licence.objects.filter(sent_at__isnull=True)

        for licence in licences_not_sent:
            schedule_licence_for_hmrc_integration(str(licence.id), licence.application.reference_code)

    def ready(self):
        if LITE_HMRC_INTEGRATION_ENABLED:
            self.initialize_background_tasks()
