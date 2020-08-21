from datetime import datetime

import django
import factory
from django.utils import timezone

from api.cases.enums import CaseTypeEnum
from api.compliance.enums import ComplianceVisitTypes, ComplianceRiskValues
from api.compliance.models import OpenLicenceReturns, ComplianceSiteCase, CompliancePerson, ComplianceVisitCase
from api.organisations.tests.factories import OrganisationFactory, SiteFactory


class OpenLicenceReturnsFactory(factory.django.DjangoModelFactory):
    returns_data = "\na,b,c,d,e"
    year = datetime.now().year

    class Meta:
        model = OpenLicenceReturns


class ComplianceSiteCaseFactory(factory.django.DjangoModelFactory):
    case_type_id = CaseTypeEnum.COMPLIANCE_SITE.id
    submitted_at = timezone.now()
    organisation = factory.SubFactory(OrganisationFactory)
    site = factory.SubFactory(SiteFactory, organisation=factory.SelfAttribute("..organisation"))

    class Meta:
        model = ComplianceSiteCase


class ComplianceVisitCaseFactory(factory.django.DjangoModelFactory):
    site_case = factory.SubFactory(
        ComplianceSiteCaseFactory,
        organisation=factory.SelfAttribute("..organisation"),
        status=factory.SelfAttribute("..status"),
    )
    case_type_id = CaseTypeEnum.COMPLIANCE_VISIT.id
    visit_type = ComplianceVisitTypes.FIRST_CONTACT
    visit_date = django.utils.timezone.now().date()
    overall_risk_value = ComplianceRiskValues.VERY_LOW
    licence_risk_value = 5
    overview = factory.Faker("word")
    inspection = factory.Faker("word")
    compliance_overview = factory.Faker("word")
    compliance_risk_value = ComplianceRiskValues.LOWER
    individuals_overview = factory.Faker("word")
    individuals_risk_value = ComplianceRiskValues.MEDIUM
    products_overview = factory.Faker("word")
    products_risk_value = ComplianceRiskValues.HIGHEST

    class Meta:
        model = ComplianceVisitCase


class PeoplePresentFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    job_title = factory.Faker("name")
    visit_case = None

    class Meta:
        model = CompliancePerson
