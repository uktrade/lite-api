from django.http import Http404

from conf.exceptions import NotFoundError
from parties.document.models import EndUserDocument
from parties.models import Party


def get_party_with_organisation(pk, organisation):
    try:
        end_user = Party.objects.get(pk=pk)

        if end_user.organisation.pk != organisation.pk:
            raise Http404

        return end_user
    except Party.DoesNotExist:
        raise NotFoundError({'parties': 'End User not found - ' + str(pk)})


def delete_end_user_document_if_exists(end_user: Party):
    try:
        end_user_document = EndUserDocument.objects.get(party=end_user)
        end_user_document.delete_s3()
        end_user_document.delete()
    except EndUserDocument.DoesNotExist:
        pass
