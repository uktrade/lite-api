from django.apps import AppConfig

from health_check.plugins import plugin_dir


class DocumentDataConfig(AppConfig):
    name = "api.document_data"

    def ready(self):
        from .health_checks import BackupDocumentDataHealthCheckBackend

        plugin_dir.register(BackupDocumentDataHealthCheckBackend)
