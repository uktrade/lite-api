from django.http import Http404

from conf.exceptions import NotFoundError
from drafts.models import Draft
from parties.document.models import EndUserDocument
from parties.models import Party, EndUser


def get_party_with_organisation(pk, organisation):
    try:
        end_user = Party.objects.get(pk=pk)

        if end_user.organisation.pk != organisation.pk:
            raise Http404

        return end_user
    except Party.DoesNotExist:
        raise NotFoundError({'parties': 'End User not found - ' + str(pk)})


def delete_end_user_and_document_document_if_exists(draft: Draft):
    try:
        end_user = EndUser.objects.get(draft=draft)
        end_user.delete()
        end_user_document = EndUserDocument.objects.get(end_user=end_user)
        end_user_document.delete_s3()
        end_user_document.delete()
    except EndUser.DoesNotExist:
        pass
    except EndUserDocument.DoesNotExist:
        pass
