from django.apps import AppConfig
from django.conf import settings


class SearchConfig(AppConfig):
    name = "api.search"

    def ready(self):
        if settings.LITE_API_ENABLE_ES:
            import api.search.signals  # noqa
