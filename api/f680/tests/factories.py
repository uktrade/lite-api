import factory
import factory.fuzzy

from faker import Faker

from django.utils import timezone

from api.cases.enums import CaseTypeEnum
from api.cases.tests.factories import LazyStatus
from api.organisations.tests.factories import OrganisationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.countries.factories import CountryFactory
from api.teams.tests.factories import TeamFactory
from api.users.tests.factories import GovUserFactory

from api.f680.enums import (
    ApprovalTypes,
    RecipientRole,
    RecipientType,
    RecommendationType,
    SecurityGrading,
    SecurityReleaseOutcomes,
)
from api.f680.models import (
    F680Application,
    Product,
    Recipient,
    Recommendation,
    SecurityReleaseRequest,
    SecurityReleaseOutcome,
)

faker = Faker()


class F680ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = F680Application

    application = {"some": "json"}
    case_type_id = CaseTypeEnum.F680.id
    organisation = factory.SubFactory(OrganisationFactory)
    status = LazyStatus(CaseStatusEnum.DRAFT)


class SubmittedF680ApplicationFactory(F680ApplicationFactory):
    status = LazyStatus(CaseStatusEnum.SUBMITTED)
    submitted_at = factory.LazyFunction(timezone.now)


class F680ProductFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda n: faker.name())
    description = factory.LazyAttribute(lambda n: faker.name())
    security_grading = factory.fuzzy.FuzzyChoice(SecurityGrading.product_choices, getter=lambda t: t[0])
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = Product


class F680RecipientFactory(factory.django.DjangoModelFactory):
    name = factory.LazyAttribute(lambda n: faker.name())
    address = factory.LazyAttribute(lambda n: faker.address())
    country = factory.SubFactory(CountryFactory)
    type = factory.fuzzy.FuzzyChoice(RecipientType.choices, getter=lambda t: t[0])
    role = factory.fuzzy.FuzzyChoice(RecipientRole.choices, getter=lambda t: t[0])
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = Recipient


class F680SecurityReleaseRequestFactory(factory.django.DjangoModelFactory):
    recipient = factory.SubFactory(F680RecipientFactory)
    product = factory.SubFactory(F680ProductFactory)
    application = factory.SubFactory(SubmittedF680ApplicationFactory)
    security_grading = factory.fuzzy.FuzzyChoice(SecurityGrading.security_release_choices, getter=lambda t: t[0])
    approval_types = factory.List(
        [
            ApprovalTypes.INITIAL_DISCUSSION_OR_PROMOTING,
            ApprovalTypes.DEMONSTRATION_OVERSEAS,
            ApprovalTypes.TRAINING,
            ApprovalTypes.SUPPLY,
        ]
    )
    intended_use = factory.LazyAttribute(lambda n: faker.name())

    class Meta:
        model = SecurityReleaseRequest


class F680RecommendationFactory(factory.django.DjangoModelFactory):
    type = factory.fuzzy.FuzzyChoice(RecommendationType.choices, getter=lambda t: t[0])
    case = factory.SubFactory(SubmittedF680ApplicationFactory)
    security_grading = factory.fuzzy.FuzzyChoice(SecurityGrading.security_release_choices, getter=lambda t: t[0])
    security_grading_other = factory.LazyAttribute(lambda n: faker.word())
    conditions = factory.LazyAttribute(lambda n: faker.sentence())
    security_release_request = factory.SubFactory(F680SecurityReleaseRequestFactory)
    user = factory.SubFactory(GovUserFactory)
    team = factory.SubFactory(TeamFactory)

    class Meta:
        model = Recommendation


class F680SecurityReleaseOutcomeFactory(factory.django.DjangoModelFactory):
    outcome = factory.fuzzy.FuzzyChoice(SecurityReleaseOutcomes.choices, getter=lambda t: t[0])
    case = factory.SubFactory(SubmittedF680ApplicationFactory)
    security_grading = factory.fuzzy.FuzzyChoice(SecurityGrading.security_release_choices, getter=lambda t: t[0])
    conditions = factory.LazyAttribute(lambda n: faker.sentence())
    user = factory.SubFactory(GovUserFactory)
    team = factory.SubFactory(TeamFactory)

    class Meta:
        model = SecurityReleaseOutcome
