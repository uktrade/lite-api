from parties.models import UltimateEndUser, ThirdParty
from drafts.libraries.get_drafts import get_draft


def get_end_user(draft_pk):
    draft = get_draft(draft_pk)
    return draft.end_user


def get_ultimate_end_user(pk):
    return UltimateEndUser.objects.get(pk=pk)


def get_consignee(draft_pk):
    draft = get_draft(draft_pk)
    return draft.consignee


def get_third_party(pk):
    return ThirdParty.objects.get(pk=pk)
