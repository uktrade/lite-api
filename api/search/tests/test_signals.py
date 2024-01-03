import json

from unittest.mock import patch

from django.test import override_settings

from api.parties.models import PartyType
from test_helpers.clients import DataTestClient


class UpdateApplicationDocumentTest(DataTestClient):
    def assertCallsAreJSONEncodable(self, mock_func):
        """Check that the args and kwargs for a mock function are all JSON
        encodable.

        This is useful to check when we know a function is used as a background
        task and we want to ensure all of the arguments its called with are
        JSON encodable as this is what the background task library will be doing
        """
        for mock_call in mock_func.mock_calls:
            try:
                json.dumps(mock_call.args)
            except TypeError:
                self.fail("Call args are not JSON encodable")

            try:
                json.dumps(mock_call.kwargs)
            except TypeError:
                self.fail("Call kwargs are not JSON encodable")

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_standard_application(self, mock_task):
        application = self.create_standard_application_case(self.organisation)

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call([("applications.BaseApplication", str(application.pk))])

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_case_assignment(self, mock_task):
        assignment = self.create_case_assignment(
            self.queue, self.create_standard_application_case(self.organisation), self.gov_user
        )

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call([("applications.BaseApplication", str(assignment.case.baseapplication.pk))])

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_case(self, mock_task):
        case = self.create_standard_application_case(self.organisation).get_case()

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call([("applications.BaseApplication", str(case.baseapplication.pk))])

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_good(self, mock_task):
        application = self.create_standard_application_case(self.organisation)
        good = self.create_good("test good", self.organisation)
        good_on_app = self.create_good_on_application(application, good)
        application.goods.add(good_on_app)
        application.save()

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call([("applications.BaseApplication", str(good_on_app.application.pk))])

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_party(self, mock_task):
        application = self.create_standard_application_case(self.organisation)
        party = self.create_party("test party", self.organisation, PartyType.END_USER, application=application)
        party.save()

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call(
            [("applications.BaseApplication", str(party.parties_on_application.all()[0].application.pk))]
        )

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_organisation(self, mock_task):
        self.create_standard_application_case(self.organisation)

        self.assertCallsAreJSONEncodable(mock_task)
        mock_task.assert_any_call(
            [("applications.BaseApplication", str(self.organisation.cases.all()[0].baseapplication.pk))]
        )

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_good_on_application_update_in_index(self, mock_task):
        application = self.create_standard_application_case(self.organisation)

        for good_on_application in application.goods.all():
            self.assertCallsAreJSONEncodable(mock_task)
            mock_task.assert_any_call([("applications.GoodOnApplication", str(good_on_application.pk))])
