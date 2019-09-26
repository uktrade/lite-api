from django.http import Http404

from applications.enums import ApplicationLicenceType
from applications.models import AbstractApplication, StandardApplication, OpenApplication
from goods.models import Good


def get_draft_type(pk):
    type = AbstractApplication.objects.get(pk=pk).licence_type

    return type


def get_drafts():
    return AbstractApplication.objects.filter(submitted_at__isnull=True)


def get_drafts_with_organisation(organisation):
    return AbstractApplication.objects.filter(organisation=organisation, submitted_at__isnull=True)


def get_draft(pk):
    draft_type = get_draft_type(pk)
    try:
        if draft_type == ApplicationLicenceType.STANDARD_LICENCE:
            return StandardApplication.objects.get(pk=pk, submitted_at__isnull=True)
        else:
            return OpenApplication.objects.get(pk=pk, submitted_at__isnull=True)
    except (StandardApplication.DoesNotExist, OpenApplication.DoesNotExist):
        raise Http404


def get_draft_with_organisation(pk, organisation):
    draft = get_draft(pk=pk)

    if draft.organisation.pk != organisation.pk:
        raise Http404

    return draft


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404
