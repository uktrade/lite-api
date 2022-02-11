import factory

from api.cases.enums import AdviceLevel, AdviceType
from api.cases.models import (
    Advice,
    Case,
    CaseAssignment,
    CaseStatus,
    CaseType,
    EcjuQuery,
    GoodCountryDecision,
    DepartmentSLA,
)
from api.queues.tests.factories import QueueFactory
from api.organisations.tests.factories import OrganisationFactory
from api.goodstype.tests.factories import GoodsTypeFactory
from api.staticdata.countries.factories import CountryFactory
from api.teams.tests.factories import TeamFactory, DepartmentFactory
from api.users.tests.factories import GovUserFactory


class UserAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.USER

    class Meta:
        model = Advice


class TeamAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.TEAM

    class Meta:
        model = Advice


class FinalAdviceFactory(factory.django.DjangoModelFactory):
    text = factory.Faker("word")
    note = factory.Faker("word")
    type = AdviceType.APPROVE
    level = AdviceLevel.FINAL

    class Meta:
        model = Advice


class GoodCountryDecisionFactory(factory.django.DjangoModelFactory):
    goods_type = factory.SubFactory(GoodsTypeFactory, application=factory.SelfAttribute("..case"))
    country = factory.SubFactory(CountryFactory)
    approve = True

    class Meta:
        model = GoodCountryDecision


class CaseFactory(factory.django.DjangoModelFactory):
    case_type = factory.Iterator(CaseType.objects.all())
    status = factory.Iterator(CaseStatus.objects.all())
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = Case


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
