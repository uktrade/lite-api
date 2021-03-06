from api.parties.models import PartyDocument
from api.parties.models import Party


def delete_party_document_if_exists(party: Party):
    try:
        document = PartyDocument.objects.get(party=party)
        document.delete_s3()
        document.delete()
    except PartyDocument.DoesNotExist:
        pass
