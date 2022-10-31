from unittest import mock

from django.core.management import call_command
from api.applications.models import PartyOnApplication, StandardApplication

from api.cases.enums import AdviceType, AdviceLevel
from api.licences.enums import LicenceStatus
from api.licences.tests.factories import GoodOnLicenceFactory
from api.licences.tests.test_api_to_hmrc_integration import MockResponse
from test_helpers.clients import DataTestClient


class TruncateEndUserNameMgmtCommandTests(DataTestClient):
    def _create_good_on_licence(self, licence, good_on_application):
        GoodOnLicenceFactory(
            good=good_on_application,
            licence=licence,
            quantity=good_on_application.quantity,
            usage=0.0,
            value=good_on_application.value,
        )

    def create_siel_licence(self):
        standard_application = self.create_standard_application_case(self.organisation)
        self.create_advice(self.gov_user, standard_application, "good", AdviceType.APPROVE, AdviceLevel.FINAL)
        licence = self.create_licence(standard_application, status=LicenceStatus.ISSUED)
        self._create_good_on_licence(licence, standard_application.goods.first())
        return licence

    @mock.patch("api.support.management.commands.truncate_end_user_name.post")
    def test_truncating_end_user_name_greater_than_80_chars(self, requests_post):
        licence = self.create_siel_licence()
        application = StandardApplication.objects.get(reference_code=licence.reference_code)
        end_user = PartyOnApplication.objects.filter(application=application, party__type="end_user").first()
        end_user.party.name = "".join("a" for i in range(100))
        end_user.party.save()

        requests_post.return_value = MockResponse("", 201)

        self.assertIsNone(licence.hmrc_integration_sent_at)
        call_command("truncate_end_user_name", licence.reference_code)

        requests_post.assert_called_once()
        licence.refresh_from_db()
        self.assertIsNotNone(licence.hmrc_integration_sent_at)

    @mock.patch("api.support.management.commands.truncate_end_user_name.post")
    def test_truncating_end_user_name_less_than_80_chars(self, requests_post):
        licence = self.create_siel_licence()
        requests_post.return_value = MockResponse("", 201)

        self.assertIsNone(licence.hmrc_integration_sent_at)
        call_command("truncate_end_user_name", licence.reference_code)
        requests_post.assert_not_called()
        self.assertIsNone(licence.hmrc_integration_sent_at)
