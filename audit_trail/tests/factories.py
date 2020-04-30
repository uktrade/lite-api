import factory

from audit_trail.enums import AuditType
from audit_trail.models import Audit


class AuditFactory(factory.django.DjangoModelFactory):
    verb = AuditType.UPDATED_STATUS

    class Meta:
        model = Audit