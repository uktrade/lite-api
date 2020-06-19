from datetime import datetime

import factory
from django.utils import timezone

from cases.enums import CaseTypeEnum
from compliance.models import OpenLicenceReturns, ComplianceSiteCase
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class OpenLicenceReturnsFactory(factory.django.DjangoModelFactory):
    returns_data = "\na,b,c,d,e"
    year = datetime.now().year

    class Meta:
        model = OpenLicenceReturns


class ComplianceSiteCaseFactory(factory.django.DjangoModelFactory):
    case_type_id = CaseTypeEnum.COMPLIANCE.id
    status = get_case_status_by_status(CaseStatusEnum.OPEN)
    submitted_at = timezone.now()

    class Meta:
        model = ComplianceSiteCase
