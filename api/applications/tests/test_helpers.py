import itertools

from elasticsearch_dsl import Index, Q, Search

from django.conf import settings

from api.applications import helpers, models
from api.flags.enums import SystemFlags
from api.parties.enums import PartyType
from test_helpers.clients import DataTestClient
from api.external_data.documents import SanctionDocumentType


def prepare_index():
    SanctionDocumentType._index.delete(ignore=[404])
    SanctionDocumentType._index.refresh()
    SanctionDocumentType._index.save()
    SanctionDocumentType._index.refresh()
    search = Search(index=SanctionDocumentType._index._name).update_from_dict({"query": {"match_all": {}}})

    for item in search.execute().hits:
        SanctionDocumentType.get(pk=item["id"]).delete()


class AbstractAutoMatchTests:
    def create_application(self):
        raise NotImplementedError

    def get_party(self, application):
        raise NotImplementedError

    def test_auto_match_sanctions_no_matches(self):
        prepare_index()

        application = self.create_application()
        party = self.get_party(application)

        helpers.auto_match_sanctions(application)

        party_on_application = application.parties.get(party=party)

        self.assertEquals(party_on_application.sanction_matches.all().count(), 0)
        self.assertEquals(party_on_application.flags.count(), 0)

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

        self.assertEquals(party_on_application.sanction_matches.count(), 1)
        self.assertEquals(party_on_application.sanction_matches.first().elasticsearch_reference, "123")
        self.assertEquals(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)

    def test_auto_match_sanctions_match_address(self):
        prepare_index()

        application = self.create_application()
        party = self.get_party(application)
        party.address = "123 Fake Street"
        party.save()

        document = SanctionDocumentType(
            name="Johnson Woodlington",
            address="123 fake street",
            flag_uuid=SystemFlags.SANCTION_UK_MATCH,
            reference="123",
        )
        document.save()
        SanctionDocumentType._index.refresh()

        helpers.auto_match_sanctions(application)

        party_on_application = application.parties.get(party=party)

        self.assertEquals(party_on_application.sanction_matches.count(), 1)
        self.assertEquals(party_on_application.sanction_matches.first().elasticsearch_reference, "123")
        self.assertEquals(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)

    def test_auto_match_sanctions_match_avoid_false_positive_similar_name_different_address(self):
        names = [
            "Jeremy Thompson",
            "Fred Jackson",
            "Jack Jeremyson",
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
                address="456 Fake Street, Berlin",
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference="123",
            )
            document.save()
            SanctionDocumentType._index.refresh()

            helpers.auto_match_sanctions(application)

            party_on_application = application.parties.get(party=party)

            self.assertEquals(party_on_application.sanction_matches.count(), 0)
            self.assertEquals(party_on_application.flags.count(), 0)

    def test_auto_match_sanctions_match_address_similar(self):
        addresses = [
            "123 Fake Street, London, E14 9IX",
            "123 Fake Street, London, E149IX",
            "123 Fake Street, London, E14 9IX",
            "123 Fake Street, London, e14 9ix",
            "123 Fake Street\nLondon\nE14 9IX",
            "123 Fake Street\nLondon\nUK\nE14 9IX",
        ]

        for address_variant in addresses:
            prepare_index()

            application = self.create_application()
            party = self.get_party(application)
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name="Jeremy Jackson",
                address=address_variant,
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference="123",
            )
            document.save()
            SanctionDocumentType._index.refresh()

            helpers.auto_match_sanctions(application)

            party_on_application = application.parties.get(party=party)

            self.assertEquals(party_on_application.sanction_matches.count(), 1, msg=f'tried "{address_variant}"')
            self.assertEquals(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)

    def test_auto_match_sanctions_match_name_similar(self):
        names = [
            "Jeremy Jackson",
            "Jackson, Jeremy",
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

            self.assertEquals(party_on_application.sanction_matches.count(), 1, msg=f'tried "{name_variant}"')
            self.assertEquals(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)

    def test_auto_match_sanctions_match_name_address_similar(self):
        names = [
            "Jeremy Jackson",
            "Jackson, Jeremy",
            "JeremyJackson",
            "J Jackson",
            "J. Jackson",
            "Mr. J Jackson",
            "Mr. Jackson",
        ]

        addresses = [
            "123 Fake Street, London",
            "123 Fake Street, London",
            "123 Fake Street, London",
            "123 Fake Street, London",
            "123 Fake Street\nLondon\n",
            "123 Fake Street\nLondon\nUK",
        ]

        postcodes = [
            "E14 9IX",
            "e14 9ix",
            "E149IX",
        ]

        for name, address, postcode in itertools.product(names, addresses, postcodes):
            prepare_index()

            application = self.create_application()
            party = self.get_party(application)
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name=name,
                address=f"{address} {postcode}",
                postcode=postcode,
                flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                reference="123",
            )
            document.save()
            SanctionDocumentType._index.refresh()
            helpers.auto_match_sanctions(application)

            party_on_application = application.parties.get(party=party)

            self.assertEquals(
                party_on_application.sanction_matches.count(), 1, msg=f'tried "{name} + "{address}" "{postcode}"'
            )
            self.assertEquals(str(party_on_application.flags.first().pk), SystemFlags.SANCTION_UK_MATCH)


class AutoMatchStandardApplicationTests(AbstractAutoMatchTests, DataTestClient):
    def create_application(self):
        return self.create_standard_application_case(self.organisation)

    def get_party(self, application):
        return application.end_user.party


class AutoMatchOpenApplicationTests(AbstractAutoMatchTests, DataTestClient):
    def create_application(self):
        application = self.create_open_application_case(self.organisation)
        self.create_party("Ultimate end User", self.organisation, PartyType.ULTIMATE_END_USER, application)
        return application

    def get_party(self, application):
        return application.ultimate_end_users[0].party
