from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    name = "api.applications"

    def ready(self):
        import api.applications.signals  # noqa
