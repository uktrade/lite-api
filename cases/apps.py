from django.apps import AppConfig


class CasesConfig(AppConfig):
    name = "cases"

    def ready(self):
        from actstream import registry
        registry.register(self.get_model('Case'))
