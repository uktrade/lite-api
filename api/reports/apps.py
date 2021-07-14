from django.apps import AppConfig
from django.db.models.signals import post_migrate

from api.conf.settings import BACKGROUND_TASK_ENABLED


class ReportsConfig(AppConfig):
    name = "api.reports"

    def initialize_background_tasks(self, **kwargs):
        from background_task.models import Task
        from api.reports.tasks import email_reports_task

        if not Task.objects.filter(task_name="api.reports.tasks.email_reports_task").exists():
            email_reports_task(repeat=Task.DAILY, repeat_until=None)  # noqa

    def ready(self):
        if BACKGROUND_TASK_ENABLED:
            post_migrate.connect(self.initialize_background_tasks, sender=self)
