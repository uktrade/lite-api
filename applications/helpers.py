from applications.models import BaseApplication
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
from cases.enums import CaseTypeExtendedEnum
from conf.exceptions import BadRequestError
from lite_content.lite_api import strings


def get_application_view_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeExtendedEnum.SubType.STANDARD:
        return StandardApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.OPEN:
        return OpenApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.HMRC:
        return HmrcQueryViewSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceViewSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_view_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_application_create_serializer(application_type):
    if application_type == CaseTypeExtendedEnum.SubType.STANDARD:
        return StandardApplicationCreateSerializer
    elif application_type == CaseTypeExtendedEnum.SubType.OPEN:
        return OpenApplicationCreateSerializer
    elif application_type == CaseTypeExtendedEnum.SubType.HMRC:
        return HmrcQueryCreateSerializer
    elif application_type == CaseTypeExtendedEnum.SubType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceCreateSerializer
    else:
        raise BadRequestError({"application_type": [strings.Applications.SELECT_A_LICENCE_TYPE]})


def get_application_update_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeExtendedEnum.SubType.STANDARD:
        return StandardApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.OPEN:
        return OpenApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.HMRC:
        return HmrcQueryUpdateSerializer
    elif application.case_type.sub_type == CaseTypeExtendedEnum.SubType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_update_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )
