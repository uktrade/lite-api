from unittest.mock import call, patch

from django.test import override_settings

from api.parties.models import PartyType
from test_helpers.clients import DataTestClient


class UpdateApplicationDocumentTest(DataTestClient):
    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_standard_application(self, mock_task):
        application = self.create_standard_application_case(self.organisation)

        assert [call([("applications.BaseApplication", application.pk)])] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_case_assignment(self, mock_task):
        assignment = self.create_case_assignment(
            self.queue, self.create_standard_application_case(self.organisation), self.gov_user
        )

        assert [
            call([("applications.BaseApplication", assignment.case.baseapplication.pk)])
        ] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_case(self, mock_task):
        case = self.create_standard_application_case(self.organisation).get_case()

        assert [call([("applications.BaseApplication", case.baseapplication.pk)])] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_good(self, mock_task):
        application = self.create_standard_application_case(self.organisation)
        good = self.create_good("test good", self.organisation)
        good_on_app = self.create_good_on_application(application, good)
        application.goods.add(good_on_app)
        application.save()

        assert [call([("applications.BaseApplication", good_on_app.application.pk)])] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_party(self, mock_task):
        application = self.create_standard_application_case(self.organisation)
        party = self.create_party("test party", self.organisation, PartyType.END_USER, application=application)
        party.save()

        assert [
            call([("applications.BaseApplication", party.parties_on_application.all()[0].application.pk)])
        ] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_organisation(self, mock_task):
        self.create_standard_application_case(self.organisation)

        assert [
            call([("applications.BaseApplication", self.organisation.cases.all()[0].baseapplication.pk)])
        ] in mock_task.call_args_list

    @override_settings(BACKGROUND_TASK_ENABLED=True, LITE_API_ENABLE_ES=True)
    @patch("api.search.signals.update_search_index")
    def test_good_on_application_update_in_index(self, mock_task):
        application = self.create_standard_application_case(self.organisation)

        for good_on_application in application.goods.all():
            assert [call([("applications.GoodOnApplication", good_on_application.pk)])] in mock_task.call_args_list
