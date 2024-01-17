import json

from unittest.mock import patch

from django.test import override_settings

from api.parties.models import PartyType
from test_helpers.clients import DataTestClient


class UpdateApplicationDocumentTest(DataTestClient):
    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_standard_application(self, mock_registry):
        application = self.create_standard_application_case(self.organisation)
        mock_registry.update.assert_any_call(application.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_case_assignment(self, mock_registry):
        assignment = self.create_case_assignment(
            self.queue, self.create_standard_application_case(self.organisation), self.gov_user
        )
        mock_registry.update.assert_any_call(assignment.case.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_case(self, mock_registry):
        case = self.create_standard_application_case(self.organisation).get_case()

        mock_registry.update.assert_any_call(case.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_good(self, mock_registry):
        application = self.create_standard_application_case(self.organisation)
        good = self.create_good("test good", self.organisation)
        good_on_app = self.create_good_on_application(application, good)
        application.goods.add(good_on_app)
        application.save()

        mock_registry.update.assert_any_call(good_on_app)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_party(self, mock_registry):
        application = self.create_standard_application_case(self.organisation)
        party = self.create_party("test party", self.organisation, PartyType.END_USER, application=application)
        party.save()

        mock_registry.update.assert_any_call(application.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_organisation(self, mock_registry):
        application_organisation = self.create_standard_application_case(self.organisation)

        mock_registry.update.assert_any_call(application_organisation.baseapplication)

    @override_settings(LITE_API_ENABLE_ES=True)
    @patch("api.search.celery_tasks.registry")
    def test_good_on_application_update_in_index(self, mock_registry):
        application = self.create_standard_application_case(self.organisation)

        for good_on_application in application.goods.all():
            mock_registry.update.assert_any_call(good_on_application)

    @override_settings(LITE_API_ENABLE_ES=False)
    @patch("api.search.celery_tasks.registry")
    def test_standard_application_with_elasticsearch_disabled(self, mock_registry):
        self.create_standard_application_case(self.organisation)
        mock_registry.update.assert_not_called()
