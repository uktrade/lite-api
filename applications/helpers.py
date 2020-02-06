from applications.enums import ApplicationType
from applications.models import BaseApplication
from applications.serializers.f_six_eighty_clearance import (
    FSixEightyClearanceCreateSerializer,
    FSixEightyClearanceViewSerializer,
    FSixEightyClearanceUpdateSerializer,
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
from conf.exceptions import BadRequestError
from lite_content.lite_api import strings


def get_application_view_serializer(application: BaseApplication):
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationViewSerializer
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationViewSerializer
    elif application.application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryViewSerializer
    elif application.application_type == ApplicationType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceViewSerializer
    elif application.application_type == ApplicationType.GIFTING_CLEARANCE:
        return GiftingClearanceViewSerializer
    elif application.application_type == ApplicationType.F_SIX_EIGHTY_CLEARANCE:
        return FSixEightyClearanceViewSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_view_serializer does "
                f"not support this application type: {application.application_type}"
            }
        )


def get_application_create_serializer(application_type):
    if application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationCreateSerializer
    elif application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationCreateSerializer
    elif application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryCreateSerializer
    elif application_type == ApplicationType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceCreateSerializer
    elif application_type == ApplicationType.GIFTING_CLEARANCE:
        return GiftingClearanceCreateSerializer
    elif application_type == ApplicationType.F_SIX_EIGHTY_CLEARANCE:
        return FSixEightyClearanceCreateSerializer
    else:
        raise BadRequestError({"application_type": [strings.Applications.SELECT_A_LICENCE_TYPE]})


def get_application_update_serializer(application: BaseApplication):
    if application.application_type == ApplicationType.STANDARD_LICENCE:
        return StandardApplicationUpdateSerializer
    elif application.application_type == ApplicationType.OPEN_LICENCE:
        return OpenApplicationUpdateSerializer
    elif application.application_type == ApplicationType.HMRC_QUERY:
        return HmrcQueryUpdateSerializer
    elif application.application_type == ApplicationType.EXHIBITION_CLEARANCE:
        return ExhibitionClearanceUpdateSerializer
    elif application.application_type == ApplicationType.GIFTING_CLEARANCE:
        return GiftingClearanceUpdateSerializer
    elif application.application_type == ApplicationType.F_SIX_EIGHTY_CLEARANCE:
        return FSixEightyClearanceUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_update_serializer does "
                f"not support this application type: {application.application_type}"
            }
        )
