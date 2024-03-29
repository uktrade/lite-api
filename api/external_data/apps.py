from elasticsearch_dsl.exceptions import IllegalOperation
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class ExternalDataConfig(AppConfig):
    name = "api.external_data"

    def ready(self):
        if settings.LITE_API_ENABLE_ES:
            post_migrate.connect(receiver=self.ensure_elasticsearch_index, sender=self)

    def ensure_elasticsearch_index(self, **kwargs):
        from api.external_data import documents

        try:
            documents.SanctionDocumentType.init()
        except IllegalOperation:
            pass
