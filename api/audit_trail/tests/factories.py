import factory

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.teams.tests.factories import TeamFactory
from api.users.enums import UserType
from api.users.tests.factories import BaseUserFactory


class AuditFactory(factory.django.DjangoModelFactory):
    actor = factory.SubFactory(
        BaseUserFactory,
        team=factory.SubFactory(TeamFactory),
        type=UserType.INTERNAL,
    )
    verb = AuditType.CREATED

    class Meta:
        model = Audit
