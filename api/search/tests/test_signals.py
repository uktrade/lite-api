import json

from unittest.mock import patch

from django.test import override_settings
from django_elasticsearch_dsl.signals import CelerySignalProcessor

from api.audit_trail.tests.factories import AuditFactory
from api.goods.tests.factories import GoodFactory
from api.search.application.documents import ApplicationDocumentType
from api.parties.models import PartyType
from test_helpers.clients import DataTestClient


class UpdateApplicationDocumentTest(DataTestClient):
    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_standard_application(self, mock_registry_update):
        application = self.create_standard_application_case(self.organisation)
        mock_registry_update.assert_any_call(application.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch.object(ApplicationDocumentType, "update")
    def test_case_assignment(self, mock_document_update):
        application = self.create_standard_application_case(self.organisation)
        mock_document_update.reset_mock()
        assignment = self.create_case_assignment(self.queue, application, self.gov_user)
        mock_document_update.assert_any_call(assignment.case.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_case(self, mock_registry_update):
        case = self.create_standard_application_case(self.organisation).get_case()

        mock_registry_update.assert_any_call(case.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_good(self, mock_registry_update):
        application = self.create_standard_application_case(self.organisation)
        good = GoodFactory(organisation=self.organisation)
        good_on_app = self.create_good_on_application(application, good)
        application.goods.add(good_on_app)
        application.save()

        mock_registry_update.assert_any_call(good_on_app)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_party(self, mock_registry_update):
        application = self.create_standard_application_case(self.organisation)
        party = self.create_party("test party", self.organisation, PartyType.END_USER, application=application)
        party.save()

        mock_registry_update.assert_any_call(application.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_organisation(self, mock_registry_update):
        application_organisation = self.create_standard_application_case(self.organisation)

        mock_registry_update.assert_any_call(application_organisation.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("django_elasticsearch_dsl.registries.registry.update")
    def test_good_on_application_update_in_index(self, mock_registry_update):
        application = self.create_standard_application_case(self.organisation)

        for good_on_application in application.goods.all():
            mock_registry_update.assert_any_call(good_on_application)


class ESDSLSignalProcessorTest(DataTestClient):

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch.object(CelerySignalProcessor, "handle_save")
    def test_handle_save_registered_model(self, mock_handle_save):
        application = self.create_standard_application_case(self.organisation)
        assert mock_handle_save.called == True

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch.object(CelerySignalProcessor, "handle_save")
    def test_handle_save_non_registered_model(self, mock_handle_save):
        audit = AuditFactory()
        assert mock_handle_save.called == False

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch.object(CelerySignalProcessor, "handle_save")
    def test_handle_save_related_registered_model(self, mock_handle_save):
        application = self.create_standard_application_case(self.organisation)
        mock_handle_save.reset_mock()
        assignment = self.create_case_assignment(self.queue, application, self.gov_user)
        assert mock_handle_save.called == True
