from api.applications.models import BaseApplication, F680Application, OpenApplication, StandardApplication
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.exceptions import NotFoundError


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    application_type = _get_application_type(pk)

    model_class = _get_application_model_class(application_type)
    return model_class.objects.get_application(pk, **kwargs)


def _get_application_type(pk):
    try:
        return BaseApplication.objects.values_list("case_type__sub_type", flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise NotFoundError({"application_type": "Application type not found - " + str(pk)})


def _get_application_model_class(application_type):
    model_classes = {
        CaseTypeSubTypeEnum.STANDARD: StandardApplication,
        CaseTypeSubTypeEnum.OPEN: OpenApplication,
        CaseTypeSubTypeEnum.F680: F680Application,
        CaseTypeSubTypeEnum.OPEN: OpenApplication,
    }
    try:
        return model_classes[application_type]
    except KeyError:
        raise NotImplementedError(f"get_application does not support this application type: {application_type}")
