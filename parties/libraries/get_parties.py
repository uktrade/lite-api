from applications.libraries.get_applications import get_application
from parties.models import UltimateEndUser, ThirdParty


def get_end_user(draft_pk):
    draft = get_application(draft_pk, submitted=False)
    return draft.end_user


def get_ultimate_end_user(pk):
    return UltimateEndUser.objects.get(pk=pk)


def get_consignee(draft_pk):
    draft = get_application(draft_pk, submitted=False)
    return draft.consignee


def get_third_party(pk):
    return ThirdParty.objects.get(pk=pk)
