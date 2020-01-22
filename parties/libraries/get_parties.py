from applications.libraries.get_applications import get_application
from parties.enums import PartyType
from parties.models import Party


def get_end_user(application_pk):
    draft = get_application(application_pk)
    return draft.end_user


def get_ultimate_end_user(pk):
    return Party.objects.get(pk=pk, type=PartyType.ULTIMATE)


def get_consignee(application_pk):
    draft = get_application(application_pk)
    return draft.consignee


def get_third_party(pk):
    return Party.objects.get(pk=pk, type=PartyType.THIRD)
