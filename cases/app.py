from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CasesConfig(AppConfig):
    name = "cases"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from cases.sla import update_cases_sla

        update_cases_sla(repeat=Task.DAILY, repeat_until=None)  # noqa

    def ready(self):
        post_migrate.connect(self.initialize_background_tasks, sender=self)
