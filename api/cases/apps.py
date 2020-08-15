from django.apps import AppConfig
from django.db.models.signals import post_migrate

from api.conf.settings import BACKGROUND_TASK_ENABLED


class CasesConfig(AppConfig):
    name = "api.cases"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from api.cases.tasks import update_cases_sla

        # Update cases SLA
        if not Task.objects.filter(task_name="api.cases.tasks.update_cases_sla").exists():
            update_cases_sla(repeat=Task.DAILY, repeat_until=None)  # noqa

    def ready(self):
        if BACKGROUND_TASK_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
