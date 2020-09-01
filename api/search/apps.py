from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = "api.search"

    def ready(self):
        import api.search.signals
