from django.http import Http404

from applications.models import AbstractApplication
from goods.models import Good


def get_applications():
    return AbstractApplication.objects.filter(submitted_at__isnull=False)


def get_applications_with_organisation(organisation):
    return AbstractApplication.objects.filter(organisation=organisation, submitted_at__isnull=False)


def get_application(pk):
    try:
        return AbstractApplication.objects.get(pk=pk, submitted_at__isnull=False)
    except AbstractApplication.DoesNotExist:
        raise Http404


def get_application_with_organisation(pk, organisation):
    try:
        application = AbstractApplication.objects.get(pk=pk, submitted_at__isnull=False)

        if application.organisation.pk != organisation.pk:
            raise Http404

        return application
    except AbstractApplication.DoesNotExist:
        raise Http404


def get_good_with_organisation(pk, organisation):
    try:
        good = Good.objects.get(pk=pk)

        if good.organisation.pk != organisation.pk:
            raise Http404

        return good
    except Good.DoesNotExist:
        raise Http404
