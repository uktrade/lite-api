from elasticsearch_dsl.exceptions import IllegalOperation

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def ensure_elasticsearch_index(sender, **kwargs):
    from api.external_data import documents

    try:
        documents.SanctionDocumentType.init()
    except IllegalOperation:
        pass


class ExternalDataConfig(AppConfig):
    name = "api.external_data"

    def ready(self):
        post_migrate.connect(receiver=ensure_elasticsearch_index, sender=self)
