from api.cases.models import Case


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    case = Case.objects.get(pk=pk, **kwargs)
    application = case.get_application()

    return application
