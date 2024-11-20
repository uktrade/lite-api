from django.apps import AppConfig

from health_check.plugins import plugin_dir


class CoreAppConfig(AppConfig):
    name = "api.core"

    def ready(self):
        from .health_checks import ServiceAvailableHealthCheck

        plugin_dir.register(ServiceAvailableHealthCheck)
