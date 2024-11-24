import factory

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.users.tests.factories import BaseUserFactory


class AuditFactory(factory.django.DjangoModelFactory):
    actor = factory.SubFactory(BaseUserFactory)
    verb = AuditType.CREATED

    class Meta:
        model = Audit
