import pytest
from parameterized import parameterized

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

    @parameterized.expand(
        [
            (
                [
                    "Jeremy Jackson",
                    "Jeremy - Jackson",
                    "Jeremy  Jackson",
                    "Jeremy . Jackson",
                    "Jeremy",
                    "Jeremy Jackson John",
                ],
                "Jeremy Jackson",
                [0, 1, 2, 3],
            ),
            (["Jeremy Jackson", "John", "Jeremy . Jackson", "Jeremy Jackson John"], "John ", [1]),
            (["Jerémy"], "Jeremy", [0]),
            (["Jeremy"], "Jerémy", [0]),
            (["Jerémy", "jeremy", "JEREMY"], "JerEmY", [0, 1, 2]),
            (["Jeremy A. Jackson"], "Jeremy A Jackson", [0]),
            (["Jeremy A Jackson", "Jeremy A. Jackson"], "Jeremy A. Jackson", [0, 1]),
            (["Jeremy - Jackson", "Jeremy -. Jackson", "Jeremy .. Jackson"], "Jeremy Jackson", [0, 1, 2]),
            (["Jeremy Jackson", "Jeremy - Jackson"], "Jeremy - Jackson", [0, 1]),
            (["Jeremy Jackson", "Jeremy, Jackson"], "Jeremy, Jackson", [0, 1]),
            (["Jeremy,, Jackson,"], "Jeremy Jackson", [0]),
            (["John O' Cafferty", "John O Cafferty"], "John O Cafferty", [0, 1]),
            (["John O' Cafferty", "John O Cafferty"], "John O' Cafferty", [0, 1]),
            (["Jeremy Jackson", "Jeremy A", "Jeremy Jeremy"], "Jeremy", []),
            (["Jeremy   Jackson", "Jeremy A", "Jeremy    Jeremy"], "Jeremy  Jackson", [0]),
            (
                [
                    "Fred Jackson",
                    "Jack Jeremyson",
                    "Fred Jackson",
                    "Jeremy Jacks",
                    "J Jackson",
                    "Mr. J Jackson",
                    "Mr. Jackson",
                ],
                "Jeremy Jackson",
                [],
            ),
        ]
    )
    @pytest.mark.elasticsearch
    def test_auto_match_sanctions_match(self, name_variants, signatory_name, expected_indices):
        """Sanctions matching uses exact matching"""
        prepare_index()
        application = self.create_application()
        party = self.get_party(application)
        party.signatory_name_euu = signatory_name
        party.address = "123 Fake Street, London, E14 9IX"
        party.save()

        for i, name_variant in enumerate(name_variants):
            document = SanctionDocumentType(
                name=name_variant,
                address="123 Fake Street, London, E14 9IX",
                postcode="E14 9IX",
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference=str(i),
            )
            document.save()

        SanctionDocumentType._index.refresh()

        helpers.auto_match_sanctions(application)
        party_on_application = application.parties.get(party=party)

        expected_names = [name_variants[i] for i in expected_indices]
        sanction_matches = list(party_on_application.sanction_matches.all().values_list("name", flat=True))
        self.assertEqual(expected_names, sanction_matches)


class AutoMatchStandardApplicationTests(AbstractAutoMatchTests, DataTestClient):
    def create_application(self):
        return self.create_standard_application_case(self.organisation)

    def get_party(self, application):
        return application.end_user.party
