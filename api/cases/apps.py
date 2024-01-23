from django.apps import AppConfig


class CasesConfig(AppConfig):
    name = "api.cases"

    def ready(self):
        from . import signals  # noqa
