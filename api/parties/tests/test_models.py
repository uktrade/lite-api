from django.forms import model_to_dict

from api.flags.models import Flag
from api.parties.tests.factories import PartyFactory
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
