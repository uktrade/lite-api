from django.http import Http404

from organisations.models import ExternalLocation


def get_external_location_by_pk(pk):
    try:
        return ExternalLocation.objects.get(pk=pk)
    except ExternalLocation.DoesNotExist:
        raise Http404


def get_external_location_with_organisation(pk, organisation):
    try:
        external_location = ExternalLocation.objects.get(pk=pk)

        if external_location.organisation.pk != organisation.pk:
            raise Http404

        return external_location
    except ExternalLocation.DoesNotExist:
        raise Http404
