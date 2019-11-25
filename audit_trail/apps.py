from django.apps import AppConfig


class AuditTrailConfig(AppConfig):
    name = "audit_trail"

    def ready(self):
        from actstream import registry
        from applications.models import StandardApplication
        from cases.models import Case

        registry.register(StandardApplication)
        registry.register(Case)
