import itertools

from elasticsearch_dsl import Index

from django.conf import settings

from api.applications import helpers, models
from test_helpers.clients import DataTestClient
from api.external_data.documents import SanctionDocumentType


index = Index(settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS)


class AutoMatchTests(DataTestClient):
    def test_auto_match_sanctions_no_matches(self):
        index.delete(ignore=[404])
        SanctionDocumentType.init()

        application = self.create_standard_application_case(self.organisation)

        helpers.auto_match_sanctions(application)

        self.assertEquals(application.sanction_matches.all().count(), 0)

    def test_auto_match_sanctions_match_name(self):
        index.delete(ignore=[404])
        SanctionDocumentType.init()

        application = self.create_standard_application_case(self.organisation)
        party = application.end_user.party
        party.signatory_name_euu = "Jim Example"
        party.save()

        document = SanctionDocumentType(
            name=party.signatory_name_euu, address="123 fake street", list_type="UN SC", reference="123",
        )
        document.save()
        index.refresh()

        helpers.auto_match_sanctions(application)

        self.assertEquals(application.sanction_matches.count(), 1)
        self.assertEquals(application.sanction_matches.first().elasticsearch_reference, "123")

    def test_auto_match_sanctions_match_address(self):
        index.delete(ignore=[404])
        SanctionDocumentType.init()

        application = self.create_standard_application_case(self.organisation)
        party = application.end_user.party
        party.address = "123 Fake Street"
        party.save()

        document = SanctionDocumentType(
            name="Johnson Woodlington", address="123 fake street", list_type="UN SC", reference="123",
        )
        document.save()
        index.refresh()

        helpers.auto_match_sanctions(application)

        self.assertEquals(application.sanction_matches.count(), 1)
        self.assertEquals(application.sanction_matches.first().elasticsearch_reference, "123")

    def test_auto_match_sanctions_match_avoid_false_positive_similar_name_different_address(self):
        names = [
            "Jeremy Thompson",
            "Fred Jackson",
            "Jack Jeremyson",
        ]
        for name_variant in names:
            index.delete(ignore=[404])
            SanctionDocumentType.init()

            application = self.create_standard_application_case(self.organisation)
            party = application.end_user.party
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Plank Street, London, E19 8NX"
            party.save()

            document = SanctionDocumentType(
                name=name_variant, address="456 Fake Street, Berlin", list_type="UN SC", reference="123",
            )
            document.save()
            index.refresh()

            helpers.auto_match_sanctions(application)

            self.assertEquals(application.sanction_matches.count(), 0)

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
            index.delete(ignore=[404])
            SanctionDocumentType.init()

            application = self.create_standard_application_case(self.organisation)
            party = application.end_user.party
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name="Jeremy Jackson", address=address_variant, list_type="UN SC", reference="123",
            )
            document.save()
            index.refresh()

            helpers.auto_match_sanctions(application)

            self.assertEquals(application.sanction_matches.count(), 1, msg=f'tried "{address_variant}"')

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
            index.delete(ignore=[404])
            SanctionDocumentType.init()

            application = self.create_standard_application_case(self.organisation)
            party = application.end_user.party
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name=name_variant,
                address="123 Fake Street, London, E14 9IX",
                postcode="E14 9IX",
                list_type="UN SC",
                reference="123",
            )
            document.save()
            index.refresh()

            helpers.auto_match_sanctions(application)

            self.assertEquals(application.sanction_matches.count(), 1, msg=f'tried "{name_variant}"')

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
            index.delete(ignore=[404])
            SanctionDocumentType.init()

            application = self.create_standard_application_case(self.organisation)
            party = application.end_user.party
            party.signatory_name_euu = "Jeremy Jackson"
            party.address = "123 Fake Street, London, E14 9IX"
            party.save()

            document = SanctionDocumentType(
                name=name, address=f"{address} {postcode}", postcode=postcode, list_type="UN SC", reference="123",
            )
            document.save()
            index.refresh()
            helpers.auto_match_sanctions(application)

            self.assertEquals(application.sanction_matches.count(), 1, msg=f'tried "{name} + "{address}" "{postcode}"')
