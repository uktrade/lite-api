from elasticsearch_dsl.exceptions import IllegalOperation
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class ExternalDataConfig(AppConfig):
    name = "api.external_data"

    def ready(self):
        if settings.LITE_API_ENABLE_ES:
            post_migrate.connect(receiver=self.ensure_elasticsearch_index, sender=self)
            if settings.BACKGROUND_TASK_ENABLED:
                post_migrate.connect(self.initialize_background_tasks, sender=self)

    def ensure_elasticsearch_index(self, **kwargs):
        from api.external_data import documents

        try:
            documents.SanctionDocumentType.init()
        except IllegalOperation:
            pass

    def initialize_background_tasks(self, **kwargs):
        self.schedule_update_sanctions()

    @staticmethod
    def schedule_update_sanctions():
        """Schedule Task to update sanctions index"""
        from background_task.models import Task
        from api.external_data.tasks import update_sanction_search_index

        if not Task.objects.filter(task_name="api.external_data.tasks.update_sanction_search_index").exists():
            update_sanction_search_index(repeat=Task.DAILY / 2, repeat_until=None)
