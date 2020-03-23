from applications.enums import ApplicationExportType
from applications.models import BaseApplication
from applications.serializers.end_use_details import (
    F680EndUseDetailsUpdateSerializer,
    OpenEndUseDetailsUpdateSerializer,
    StandardEndUseDetailsUpdateSerializer,
)
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
from applications.serializers.temporary_export_details import TemporaryExportDetailsUpdateSerializer
from cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum
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


def get_application_create_serializer(case_type):
    sub_type = CaseTypeEnum.reference_to_class(case_type).sub_type

    if sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceCreateSerializer
    else:
        raise BadRequestError({"application_type": [strings.Applications.Generic.SELECT_A_LICENCE_TYPE]})


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


def get_application_end_use_details_update_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardEndUseDetailsUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenEndUseDetailsUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680EndUseDetailsUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_end_use_details_update_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_temp_export_details_update_serializer(export_type):
    if export_type == ApplicationExportType.TEMPORARY:
        return TemporaryExportDetailsUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_temp_export_details_update_serializer does "
                f"not support this export type: {export_type}"
            }
        )
