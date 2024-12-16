from django.db import transaction
from rest_framework.exceptions import ParseError
from string import ascii_uppercase

from api.applications.models import GoodOnApplication
from api.applications.serializers.good import GoodOnApplicationViewSerializer
from api.cases.enums import CaseTypeSubTypeEnum
from api.licences.models import Licence
from lite_content.lite_api import strings
from api.staticdata.statuses.enums import CaseStatusEnum


@transaction.atomic
def get_licence_reference_code(application_reference):
    # Needs to lock so that 2 Licences don't get the same reference code
    total_reference_codes = (
        Licence.objects.filter(reference_code__icontains=application_reference).select_for_update().count()
    )
    return (
        f"{application_reference}/{ascii_uppercase[total_reference_codes-1]}"
        if total_reference_codes != 0
        else application_reference
    )


def serialize_goods_on_licence(licence):
    from api.licences.serializers.view_licence import GoodOnLicenceViewSerializer  # pragma: no cover

    if licence.goods.exists():
        # Standard Application
        return GoodOnLicenceViewSerializer(licence.goods, many=True).data
    elif licence.case.case_type.sub_type != CaseTypeSubTypeEnum.STANDARD:
        # MOD clearances
        goods = GoodOnApplication.objects.filter(application=licence.case.baseapplication)
        return GoodOnApplicationViewSerializer(goods, many=True).data


def update_licence_status(case, status):
    if status in [CaseStatusEnum.SURRENDERED, CaseStatusEnum.SUSPENDED, CaseStatusEnum.REVOKED]:
        try:
            licence = Licence.objects.get_active_licence(case)
            if status == CaseStatusEnum.SURRENDERED:
                licence.surrender()
            elif status == CaseStatusEnum.SUSPENDED:
                licence.suspend()
            elif status == CaseStatusEnum.REVOKED:
                licence.revoke()
        except Licence.DoesNotExist:
            raise ParseError({"status": [strings.Applications.Generic.Finalise.Error.SURRENDER]})
