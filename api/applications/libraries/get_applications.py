from api.applications.models import (
    BaseApplication,
    F680ClearanceApplication,
    GiftingClearanceApplication,
    OpenApplication,
    StandardApplication,
    HmrcQuery,
    ExhibitionClearanceApplication,
)
from cases.enums import CaseTypeSubTypeEnum
from api.conf.exceptions import NotFoundError


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    application_type = _get_application_type(pk)

    try:
        if application_type == CaseTypeSubTypeEnum.STANDARD:
            return StandardApplication.objects.get(pk=pk, **kwargs)
        elif application_type == CaseTypeSubTypeEnum.OPEN:
            return OpenApplication.objects.get(pk=pk, **kwargs)
        elif application_type == CaseTypeSubTypeEnum.HMRC:
            return HmrcQuery.objects.get(pk=pk)
        elif application_type == CaseTypeSubTypeEnum.EXHIBITION:
            return ExhibitionClearanceApplication.objects.get(pk=pk)
        elif application_type == CaseTypeSubTypeEnum.GIFTING:
            return GiftingClearanceApplication.objects.get(pk=pk)
        elif application_type == CaseTypeSubTypeEnum.F680:
            return F680ClearanceApplication.objects.get(pk=pk)
        else:
            raise NotImplementedError(f"get_application does not support this application type: {application_type}")
    except (
        StandardApplication.DoesNotExist,
        OpenApplication.DoesNotExist,
        HmrcQuery.DoesNotExist,
    ):
        raise NotFoundError({"application": "Application not found - " + str(pk)})


def _get_application_type(pk):
    try:
        return BaseApplication.objects.values_list("case_type__sub_type", flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise NotFoundError({"application_type": "Application type not found - " + str(pk)})
