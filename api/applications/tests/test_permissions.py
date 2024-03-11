from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from rest_framework.permissions import IsAdminUser

from test_helpers.clients import DataTestClient
from api.core.authentication import ORGANISATION_ID
from api.parties.tests.factories import PartyDocumentFactory, PartyFactory
from api.organisations.tests.factories import OrganisationFactory
from api.applications.permissions import IsPartyDocumentInOrganisation


class IsPartyDocumentInOrganisationTest(DataTestClient):
    def test_permissions_success(self):
        organisation = OrganisationFactory()
        party = PartyFactory(organisation=organisation)
        party_document = PartyDocumentFactory(party=party, s3_key="somekey")
        factory = RequestFactory()

        request = factory.get("/")
        request.META[ORGANISATION_ID] = organisation.id

        authorised = IsPartyDocumentInOrganisation().has_object_permission(request, None, party_document)

        self.assertTrue(authorised)

    def test_permissions_failure(self):
        organisation = OrganisationFactory()
        other_organisation = OrganisationFactory()
        party = PartyFactory(organisation=organisation)
        party_document = PartyDocumentFactory(party=party, s3_key="somekey")
        factory = RequestFactory()

        request = factory.get("/")
        request.META[ORGANISATION_ID] = other_organisation.id

        authorised = IsPartyDocumentInOrganisation().has_object_permission(request, None, party_document)

        self.assertFalse(authorised)
