from django.apps import AppConfig
from django.db.models.signals import post_migrate

from conf.settings import BACKGROUND_TASK_ENABLED, LITE_HMRC_INTEGRATION_ENABLED
from licences.enums import LicenceStatus


class CasesConfig(AppConfig):
    name = "cases"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from cases.sla import update_cases_sla

        # Update cases SLA
        if not Task.objects.filter(task_name="cases.sla.update_cases_sla").exists():
            update_cases_sla(repeat=Task.DAILY, repeat_until=None)  # noqa

        if LITE_HMRC_INTEGRATION_ENABLED:
            CasesConfig.schedule_not_sent_licences()

    @staticmethod
    def schedule_not_sent_licences():
        """
        Send licence information to HMRC integration.
        DO NOT move this into its own apps.py;
        Background tasks will be created, but do NOT get executed (for whatever reason) if there are multiple
        post_migrate hooks
        """

        from licences.models import Licence
        from licences.tasks import schedule_licence_for_hmrc_integration

        licences_not_sent = Licence.objects.filter(hmrc_integration_sent_at__isnull=True).exclude(
            status=LicenceStatus.DRAFT
        )

        for licence in licences_not_sent:
            schedule_licence_for_hmrc_integration(str(licence.id), licence.application.reference_code)

    def ready(self):
        if BACKGROUND_TASK_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
