import factory

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit


class AuditFactory(factory.django.DjangoModelFactory):
    verb = AuditType.UPDATED_STATUS

    class Meta:
        model = Audit
