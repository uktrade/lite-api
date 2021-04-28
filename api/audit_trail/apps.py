from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    name = "api.audit_trail"

    def ready(self):
        import api.audit_trail.signals  # noqa
