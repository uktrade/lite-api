import factory

from api.cases.enums import AdviceLevel, AdviceType, CaseTypeEnum
from api.cases.models import (
    Advice,
    CountersignAdvice,
    Case,
    CaseAssignment,
    CaseNote,
    CaseStatus,
    CaseType,
    EcjuQuery,
    DepartmentSLA,
)
from api.queues.tests.factories import QueueFactory
from api.organisations.tests.factories import OrganisationFactory
from api.teams.tests.factories import TeamFactory, DepartmentFactory
from api.users.tests.factories import BaseUserFactory, GovUserFactory


class CaseFactory(factory.django.DjangoModelFactory):
    case_type = factory.Iterator(CaseType.objects.all())
    status = factory.Iterator(CaseStatus.objects.all())
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = Case


class BaseAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    case = factory.SubFactory(CaseFactory)

    @factory.post_generation
    def denial_reasons(self, create, extracted, **kwargs):
        if not create:
            return

        if self.type == AdviceType.REFUSE:
            denial_reasons = extracted or ["1a", "1b", "1c"]
            self.denial_reasons.set(denial_reasons)

    class Meta:
        model = Advice


class UserAdviceFactory(BaseAdviceFactory):
    level = AdviceLevel.USER


class TeamAdviceFactory(BaseAdviceFactory):
    level = AdviceLevel.TEAM


class FinalAdviceFactory(BaseAdviceFactory):
    level = AdviceLevel.FINAL


class CountersignAdviceFactory(factory.django.DjangoModelFactory):
    order = factory.Faker("pyint", min_value=1, max_value=5)
    valid = True
    outcome_accepted = factory.Faker("pybool")
    reasons = factory.Faker("word")
    countersigned_user = factory.SubFactory(GovUserFactory)

    class Meta:
        model = CountersignAdvice


class CaseSIELFactory(CaseFactory):
    case_type_id = CaseTypeEnum.SIEL.id


class CaseTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CaseType


class DepartmentSLAFactory(factory.django.DjangoModelFactory):
    sla_days = factory.Faker("pyint", min_value=0, max_value=30)
    case = factory.SubFactory(CaseFactory)
    department = factory.SubFactory(DepartmentFactory)

    class Meta:
        model = DepartmentSLA


class CaseAssignmentFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(CaseFactory)
    user = factory.SubFactory(GovUserFactory)
    queue = factory.SubFactory(QueueFactory)

    class Meta:
        model = CaseAssignment


class EcjuQueryFactory(factory.django.DjangoModelFactory):
    question = "why x in y?"
    response = "because of z"
    case = factory.SubFactory(CaseFactory)
    team = factory.SubFactory(TeamFactory)
    raised_by_user = factory.SubFactory(GovUserFactory)

    class Meta:
        model = EcjuQuery


class CaseNoteFactory(factory.django.DjangoModelFactory):
    case = factory.SubFactory(CaseFactory)
    user = factory.SubFactory(BaseUserFactory)

    class Meta:
        model = CaseNote
