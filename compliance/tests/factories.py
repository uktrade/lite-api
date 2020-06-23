from datetime import datetime

import factory
from django.utils import timezone

from cases.enums import CaseTypeEnum
from compliance.models import OpenLicenceReturns, ComplianceSiteCase, CompliancePerson


class OpenLicenceReturnsFactory(factory.django.DjangoModelFactory):
    returns_data = "\na,b,c,d,e"
    year = datetime.now().year

    class Meta:
        model = OpenLicenceReturns


class ComplianceSiteCaseFactory(factory.django.DjangoModelFactory):
    case_type_id = CaseTypeEnum.COMPLIANCE_SITE.id
    submitted_at = timezone.now()

    class Meta:
        model = ComplianceSiteCase


class PeoplePresentFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    job_title = factory.Faker("name")
    visit_case = None

    class Meta:
        model = CompliancePerson
