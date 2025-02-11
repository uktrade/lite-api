from api.cases.models import Case
from api.core.exceptions import NotFoundError


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    try:
        case = Case.objects.get(pk=pk, **kwargs)
    except Case.DoesNotExist:
        raise NotFoundError(f"Case with id {pk} does not exist")
    application = case.get_application()
    return application
