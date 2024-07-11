from django.forms import model_to_dict
from django.utils import timezone

from api.flags.models import Flag
from api.parties.models import PartyDocument
from api.parties.tests.factories import PartyFactory, PartyDocumentFactory
from api.staticdata.countries.models import Country

from test_helpers.clients import DataTestClient


class TestParty(DataTestClient):

    def test_clone(self):
        original_party = PartyFactory(
            name="some party",
            address="123 fake st",
            country=Country.objects.get(id="FR"),
            website="https://www.example.com/foo",
            signatory_name_euu="some signatory name",
            type="end_user",
            organisation=self.organisation,
            role="intermediate_consignee",
            role_other="some other role",
            sub_type="government",
            sub_type_other="some other sub type",
            end_user_document_available=False,
            end_user_document_missing_reason="some reason",
            product_differences_note="some differences",
            document_in_english=True,
            document_on_letterhead=True,
            ec3_missing_reason="some reason",
            clearance_level="uk_official",
            descriptors="some descriptors",
            copy_of=PartyFactory(),
            phone_number="12345",
            email="some.email@example.net",  # /PS-IGNORE
            details="some details",
        )
        original_party.flags.add(Flag.objects.first())
        original_party_document = PartyDocumentFactory(party=original_party, s3_key="some key")

        cloned_party = original_party.clone()
        assert original_party.id != cloned_party.id
        assert model_to_dict(cloned_party) == {
            "name": "some party",
            "address": "123 fake st",
            "country": original_party.country.id,
            "website": "https://www.example.com/foo",
            "signatory_name_euu": "some signatory name",
            "type": "end_user",
            "organisation": original_party.organisation.id,
            "role": "intermediate_consignee",
            "role_other": "some other role",
            "sub_type": "government",
            "sub_type_other": "some other sub type",
            "end_user_document_available": False,
            "end_user_document_missing_reason": "some reason",
            "product_differences_note": "some differences",
            "document_in_english": True,
            "document_on_letterhead": True,
            "ec3_missing_reason": "some reason",
            "clearance_level": "uk_official",
            "descriptors": "some descriptors",
            "copy_of": original_party.id,
            "phone_number": "12345",
            "email": "some.email@example.net",  # /PS-IGNORE
            "details": "some details",
            "flags": [],
        }, """
        The attributes on the cloned record were not as expected. If this is the result
        of a schema migration, think carefully about whether the new fields should be
        cloned by default or not and adjust Party.clone_* attributes accordingly.
        """
        assert PartyDocument.objects.filter(party=cloned_party).count() == 1


class TestPartyDocument(DataTestClient):

    def test_clone(self):
        scanned_at_time = timezone.now()
        original_party = PartyFactory()
        original_party_document = PartyDocumentFactory(
            party=original_party,
            description="some description",
            name="some name",
            s3_key="some key",
            safe=True,
            size=100,
            type="supporting_document",
            virus_scanned_at=scanned_at_time,
        )
        new_party = PartyFactory()

        cloned_party_document = original_party_document.clone(party=new_party)
        assert original_party_document.id != cloned_party_document.id
        assert original_party_document.document_ptr != cloned_party_document.document_ptr
        assert model_to_dict(cloned_party_document) == {
            "description": "some description",
            "document_ptr": cloned_party_document.document_ptr.id,
            "name": "some name",
            "party": new_party.id,
            "s3_key": "some key",
            "safe": True,
            "size": 100,
            "type": "supporting_document",
            "virus_scanned_at": scanned_at_time,
        }
