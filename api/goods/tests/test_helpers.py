import datetime

from parameterized import parameterized

from django.utils import timezone

from api.organisations.enums import OrganisationDocumentType
from api.organisations.models import DocumentOnOrganisation
from api.organisations.tests.factories import DocumentOnOrganisationFactory
from test_helpers.clients import DataTestClient

from ..helpers import has_valid_certificate


class HasValidCertificateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.assertFalse(DocumentOnOrganisation.objects.exists())

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_no_documents(self, document_type):
        self.assertFalse(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_past_date(self, document_type):
        expiry_date = timezone.now() - datetime.timedelta(days=5)
        DocumentOnOrganisationFactory.create(
            document_type=document_type,
            organisation=self.organisation,
            expiry_date=expiry_date,
        )
        self.assertFalse(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_same_date(self, document_type):
        expiry_date = timezone.now()
        DocumentOnOrganisationFactory.create(
            document_type=document_type,
            organisation=self.organisation,
            expiry_date=expiry_date,
        )
        self.assertFalse(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_future_date(self, document_type):
        expiry_date = timezone.now() + datetime.timedelta(days=5)
        DocumentOnOrganisationFactory.create(
            document_type=document_type,
            organisation=self.organisation,
            expiry_date=expiry_date,
        )
        self.assertTrue(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_multiple_documents_of_same_type(self, document_type):
        past_expiry_date = timezone.now() - datetime.timedelta(days=5)
        same_expiry_date = timezone.now()
        future_expiry_date = timezone.now() + datetime.timedelta(days=5)

        for expiry_date in [
            past_expiry_date,
            same_expiry_date,
            future_expiry_date,
        ]:
            DocumentOnOrganisationFactory.create(
                document_type=document_type,
                organisation=self.organisation,
                expiry_date=expiry_date,
            )

        self.assertTrue(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )

    @parameterized.expand(OrganisationDocumentType.keys())
    def test_multiple_documents_of_same_type_with_explicit_uuid(self, document_type):
        # This test exists to make sure that the order of the documents isn't of
        # importance.
        # There was a case where the uuid was affecting the order of checking
        # the documents whereas the checking of the expiration date when an
        # organisation of multiple documents should not be reliant on any form
        # of ordering
        past_expiry_date = timezone.now() - datetime.timedelta(days=5)
        same_expiry_date = timezone.now()
        future_expiry_date = timezone.now() + datetime.timedelta(days=5)

        for expiry_date, pk in [
            (past_expiry_date, "11111111-1111-1111-1111-111111111111"),
            (same_expiry_date, "22222222-2222-2222-2222-222222222222"),
            (future_expiry_date, "33333333-3333-3333-3333-333333333333"),
        ]:
            DocumentOnOrganisationFactory.create(
                id=pk,
                document_type=document_type,
                organisation=self.organisation,
                expiry_date=expiry_date,
            )

        self.assertTrue(
            has_valid_certificate(
                self.organisation.id,
                document_type,
            ),
        )
