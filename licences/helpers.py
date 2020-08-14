from string import ascii_uppercase

from django.db import transaction
from rest_framework.exceptions import ParseError

from applications.models import GoodOnApplication
from applications.serializers.good import GoodOnApplicationViewSerializer
from cases.enums import CaseTypeSubTypeEnum
from cases.models import GoodCountryDecision
from api.conf.exceptions import NotFoundError
from licences.models import Licence
from lite_content.lite_api import strings
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum


def get_open_general_export_licence_case(pk):
    from open_general_licences.models import OpenGeneralLicenceCase

    try:
        return OpenGeneralLicenceCase.objects.get(pk=pk)
    except OpenGeneralLicenceCase.DoesNotExist:
        raise NotFoundError({"open_general_licence_case": "Open general licence case not found - " + str(pk)})


def get_approved_goods_types(application):
    approved_goods = GoodCountryDecision.objects.filter(case_id=application.id).values_list("goods_type", flat=True)
    return application.goods_type.filter(id__in=approved_goods)


def get_approved_countries(application):
    approved_countries = GoodCountryDecision.objects.filter(case_id=application.id).values_list("country", flat=True)
    return Country.objects.filter(id__in=approved_countries).order_by("name")


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
    from licences.serializers.view_licence import GoodOnLicenceViewSerializer, GoodsTypeOnLicenceListSerializer

    if licence.goods.exists():
        # Standard Application
        return GoodOnLicenceViewSerializer(licence.goods, many=True).data
    elif licence.case.baseapplication.goods_type.exists():
        # Open Application
        approved_goods_types = get_approved_goods_types(licence.case.baseapplication)
        return GoodsTypeOnLicenceListSerializer(approved_goods_types, many=True).data
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
