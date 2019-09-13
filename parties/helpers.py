from django.http import Http404

from conf.exceptions import NotFoundError
from parties.document.models import PartyDocument
from parties.models import EndUser, Party


def get_end_user_with_organisation(pk, organisation):
    try:
        end_user = EndUser.objects.get(pk=pk)

        if end_user.organisation.pk != organisation.pk:
            raise Http404

        return end_user
    except EndUser.DoesNotExist:
        raise NotFoundError({'end_user': 'End User not found - ' + str(pk)})


def delete_party_document_if_exists(party: Party):
    try:
        document = PartyDocument.objects.get(party=party)
        document.delete_s3()
        document.delete()
    except PartyDocument.DoesNotExist:
        pass
