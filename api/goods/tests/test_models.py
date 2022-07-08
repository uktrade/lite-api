from parameterized import parameterized

from api.applications.models import GoodOnApplication
from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    StandardApplicationFactory,
)
from api.goods.enums import GoodStatus
from api.staticdata.control_list_entries.models import ControlListEntry
from test_helpers.clients import DataTestClient

from .factories import GoodFactory


class GoodTests(DataTestClient):
    def setUp(self):
        super().setUp()

    @parameterized.expand(
        [
            GoodStatus.DRAFT,
            GoodStatus.SUBMITTED,
            GoodStatus.QUERY,
        ],
    )
    def test_get_precedents_unverified(self, good_status):
        good = GoodFactory(
            organisation=self.organisation,
            status=good_status,
        )
        good.save()

        good_on_application_with_null_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
            control_list_entries=None,
        )
        good_on_application_with_null_cles.save()
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

        good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        good_on_application_with_cles.save()
        good_on_application_with_cles.control_list_entries.add(
            ControlListEntry.objects.first(),
        )
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

    def test_get_precedents_verified(self):
        good = GoodFactory(
            organisation=self.organisation,
            status=GoodStatus.VERIFIED,
        )
        good.save()

        good_on_application_with_null_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
            control_list_entries=None,
        )
        good_on_application_with_null_cles.save()
        self.assertQuerysetEqual(
            good.get_precedents(),
            GoodOnApplication.objects.none(),
        )

        good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        good_on_application_with_cles.save()
        control_list_entry = ControlListEntry.objects.first()
        good_on_application_with_cles.control_list_entries.add(control_list_entry)
        self.assertQuerysetEqual(
            good.get_precedents(),
            [good_on_application_with_cles],
        )

        another_good_on_application_with_cles = GoodOnApplicationFactory(
            application=StandardApplicationFactory(),
            good=good,
        )
        another_good_on_application_with_cles.save()
        control_list_entry = ControlListEntry.objects.first()
        another_good_on_application_with_cles.control_list_entries.add(control_list_entry)
        self.assertQuerysetEqual(
            good.get_precedents(),
            [good_on_application_with_cles, another_good_on_application_with_cles],
        )
