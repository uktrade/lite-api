from django.apps import AppConfig


class ApplicationManifestsConfig(AppConfig):
    name = "api.application_manifests"

    def ready(self):
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("application_manifest")
