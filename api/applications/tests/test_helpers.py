import pytest

from api.applications import helpers
from api.flags.enums import SystemFlags
from test_helpers.clients import DataTestClient
from api.external_data.documents import SanctionDocumentType


def prepare_index():
    SanctionDocumentType._index.delete(ignore=[404])
    SanctionDocumentType.init()


class AbstractAutoMatchTests:
    def create_application(self):
        raise NotImplementedError

    def get_party(self, application):
        raise NotImplementedError

    @pytest.mark.elasticsearch
    def test_auto_match_sanctions_no_matches(self):
        prepare_index()

        application = self.create_application()
        party = self.get_party(application)

        helpers.auto_match_sanctions(application)

        party_on_application = application.parties.get(party=party)

        self.assertEqual(party_on_application.sanction_matches.all().count(), 0)
        self.assertEqual(party_on_application.flags.count(), 0)

    @pytest.mark.elasticsearch
    def test_auto_match_sanctions_match_name(self):
        prepare_index()

        application = self.create_application()

        party = self.get_party(application)
        party.signatory_name_euu = "Jim Example"
        party.save()

        document = SanctionDocumentType(
            name=party.signatory_name_euu,
            address="123 fake street",
            flag_uuid=SystemFlags.SANCTION_UK_MATCH,
            reference="123",
        )
        document.save()
        SanctionDocumentType._index.refresh()

        helpers.auto_match_sanctions(application)

        party_on_application = application.parties.get(party=party)

        self.assertEqual(party_on_application.sanction_matches.count(), 1)
        self.assertEqual(party_on_application.sanction_matches.first().elasticsearch_reference, "123")
        self.assertEqual(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)

    @pytest.mark.elasticsearch
    def test_auto_match_sanctions_avoid_false_positives(self):
        names = [
            "Jeremy Thompson",
            "Fred Jackson",
            "Jack Jeremyson",
            "Jeremy Jacks",
            "JeremyJackson",
            "J Jackson",
            "J. Jackson",
            "Mr. J Jackson",
            "Mr. Jackson",
        ]
        for name_variant in names:
            prepare_index()

            application = self.create_application()
            party = self.get_party(application)
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Plank Street, London, E19 8NX"
            party.save()

            document = SanctionDocumentType(
                name=name_variant,
                address="123 Plank Street, London, E19 8NX",
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference="123",
            )
            document.save()
            SanctionDocumentType._index.refresh()

            helpers.auto_match_sanctions(application)

            party_on_application = application.parties.get(party=party)

            self.assertEqual(party_on_application.sanction_matches.count(), 0)
            self.assertEqual(party_on_application.flags.count(), 0)

    @pytest.mark.elasticsearch
    def test_auto_match_sanctions_match_name_exact(self):
        """Sanctions matching uses phrase matching
        Any name that martches in search term will be returned
        """
        names = [
            "Jeremy Jackson",
            "Mr. Jeremy Jackson",
        ]

        for name_variant in names:
            prepare_index()

            application = self.create_application()
            party = self.get_party(application)
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name=name_variant,
                address="123 Fake Street, London, E14 9IX",
                postcode="E14 9IX",
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference="123",
            )
            document.save()
            SanctionDocumentType._index.refresh()

            helpers.auto_match_sanctions(application)

            party_on_application = application.parties.get(party=party)

            self.assertEqual(party_on_application.sanction_matches.count(), 1, msg=f'tried "{name_variant}"')
            self.assertEqual(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)


class AutoMatchStandardApplicationTests(AbstractAutoMatchTests, DataTestClient):
    def create_application(self):
        return self.create_standard_application_case(self.organisation)

    def get_party(self, application):
        return application.end_user.party
