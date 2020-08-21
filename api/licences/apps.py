from django.apps import AppConfig
from django.db.models.signals import post_migrate

from api.conf.settings import LITE_HMRC_INTEGRATION_ENABLED, BACKGROUND_TASK_ENABLED
from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action


class LicencesConfig(AppConfig):
    name = "api.licences"

    def initialize_background_tasks(self, **kwargs):
        self.schedule_expire_licences_task()

        if LITE_HMRC_INTEGRATION_ENABLED:
            self.schedule_not_sent_licences()

    @staticmethod
    def schedule_expire_licences_task():
        """Schedule Task to expire Licences"""

        from background_task.models import Task
        from api.licences.tasks import expire_licences

        if not Task.objects.filter(task_name="api.licences.tasks.expire_licences").exists():
            expire_licences(repeat=Task.DAILY, repeat_until=None)  # noqa

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
        if BACKGROUND_TASK_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
