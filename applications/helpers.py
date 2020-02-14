from applications.models import BaseApplication
from applications.serializers.f680_clearance import (
    F680ClearanceCreateSerializer,
    F680ClearanceViewSerializer,
    F680ClearanceUpdateSerializer,
)
from applications.serializers.gifting_clearance import (
    GiftingClearanceCreateSerializer,
    GiftingClearanceViewSerializer,
    GiftingClearanceUpdateSerializer,
)
from applications.serializers.hmrc_query import (
    HmrcQueryCreateSerializer,
    HmrcQueryViewSerializer,
    HmrcQueryUpdateSerializer,
)
from applications.serializers.open_application import (
    OpenApplicationCreateSerializer,
    OpenApplicationUpdateSerializer,
    OpenApplicationViewSerializer,
)
from applications.serializers.standard_application import (
    StandardApplicationCreateSerializer,
    StandardApplicationUpdateSerializer,
    StandardApplicationViewSerializer,
)
from applications.serializers.exhibition_clearance import (
    ExhibitionClearanceCreateSerializer,
    ExhibitionClearanceViewSerializer,
    ExhibitionClearanceUpdateSerializer,
)
from cases.enums import CaseTypeSubTypeEnum
from conf.exceptions import BadRequestError
from lite_content.lite_api import strings


def get_application_view_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceViewSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_view_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_application_create_serializer(application_case_type_sub_type):
    if application_case_type_sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationCreateSerializer
    elif application_case_type_sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationCreateSerializer
    elif application_case_type_sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryCreateSerializer
    elif application_case_type_sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceCreateSerializer
    elif application_case_type_sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceCreateSerializer
    elif application_case_type_sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceCreateSerializer
    else:
        raise BadRequestError({"case_type": [strings.Applications.SELECT_A_LICENCE_TYPE]})


def get_application_update_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_update_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )
