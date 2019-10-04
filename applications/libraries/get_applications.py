from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import BaseApplication, OpenApplication, StandardApplication
from goods.models import Good


def _get_application_from_model(pk, model):
    try:
        return model.objects.get(pk=pk, submitted_at__isnull=False)
    except model.DoesNotExist:
        raise Http404


def get_applications():
    return BaseApplication.objects.filter(submitted_at__isnull=False)


def get_applications_for_organisation(organisation):
    return BaseApplication.objects.filter(organisation=organisation, submitted_at__isnull=False)


def get_draft_type(pk):
    try:
        return BaseApplication.objects.get(pk=pk).licence_type
    except BaseApplication.DoesNotExist:
        raise Http404


def get_draft(pk):
    draft_type = get_draft_type(pk)
    try:
        if draft_type == ApplicationLicenceType.STANDARD_LICENCE:
            return StandardApplication.objects.get(pk=pk, submitted_at__isnull=True)
        else:
            return OpenApplication.objects.get(pk=pk, submitted_at__isnull=True)
    except (StandardApplication.DoesNotExist, OpenApplication.DoesNotExist):
        raise Http404


def get_application_for_organisation(pk, organisation):
    application = get_application(pk)

    if application.organisation.pk != organisation.pk:
        raise Http404

    return application


def get_application(pk):
    return _get_application_from_model(pk, BaseApplication)


def get_open_application(pk):
    return _get_application_from_model(pk, OpenApplication)


def get_standard_application(pk):
    return _get_application_from_model(pk, StandardApplication)


def get_good_for_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404


def get_draft_applications():
    return BaseApplication.objects.filter(submitted_at__isnull=True)


def get_draft_applications_for_organisation(organisation):
    return BaseApplication.objects.filter(organisation=organisation, submitted_at__isnull=True)


def get_draft_application_for_organisation(pk, organisation):
    draft = get_draft(pk=pk)

    if draft.organisation.pk != organisation.pk:
        raise Http404

    return draft
