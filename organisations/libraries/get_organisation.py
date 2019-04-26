from django.http import Http404

from organisations.models import Organisation


def get_organisation_by_pk(pk):
    try:
        return Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        raise Http404


def get_organisation_by_user(user):
    if not user.organisation:
        raise Http404

    return user.organisation
