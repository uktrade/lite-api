from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import BaseApplication, OpenApplication, StandardApplication
from goods.models import Good


def get_applications():
    return BaseApplication.objects.filter(submitted_at__isnull=False)


def get_applications_with_organisation(organisation):
    return BaseApplication.objects.filter(organisation=organisation, submitted_at__isnull=False)


def get_application_with_organisation(pk, organisation):
    try:
        application = BaseApplication.objects.get(pk=pk, submitted_at__isnull=False)

        if application.organisation.pk != organisation.pk:
            raise Http404

        return application
    except BaseApplication.DoesNotExist:
        raise Http404


def get_draft_type(pk):
    try:
        type = BaseApplication.objects.get(pk=pk).licence_type
        return type
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


def get_application(pk):
    try:
        return BaseApplication.objects.get(pk=pk, submitted_at__isnull=False)
    except BaseApplication.DoesNotExist:
        raise Http404


def get_open_application(pk):
    try:
        return OpenApplication.objects.get(pk=pk, submitted_at__isnull=False)
    except OpenApplication.DoesNotExist:
        raise Http404


def get_standard_application(pk):
    try:
        return StandardApplication.objects.get(pk=pk, submitted_at__isnull=False)
    except StandardApplication.DoesNotExist:
        raise Http404


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404




def get_drafts():
    return BaseApplication.objects.filter(submitted_at__isnull=True)


def get_drafts_with_organisation(organisation):
    return BaseApplication.objects.filter(organisation=organisation, submitted_at__isnull=True)


def get_draft_with_organisation(pk, organisation):
    draft = get_draft(pk=pk)

    if draft.organisation.pk != organisation.pk:
        raise Http404

    return draft
