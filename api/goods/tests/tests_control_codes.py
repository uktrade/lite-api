from django.urls import reverse_lazy
from parameterized import parameterized
from rest_framework import status

from api.applications.models import GoodOnApplication
from api.core import constants
from api.flags.enums import FlagLevels
from api.flags.tests.factories import FlagFactory
from api.goods.enums import GoodControlled
from api.goods.models import Good
from api.goods.tests.factories import GoodFactory
from api.goodstype.tests.factories import GoodsTypeFactory
from api.picklists.enums import PicklistType, PickListStatus
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.units.enums import Units
from test_helpers.clients import DataTestClient
from test_helpers.helpers import is_not_verified_flag_set_on_good
from api.users.models import Role, GovUser


class GoodsVerifiedTestsStandardApplication(DataTestClient):
    def setUp(self):
        super().setUp()

        self.report_summary = self.create_picklist_item(
            "Report Summary", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE
        )

        self.good_1 = GoodFactory(
            organisation=self.organisation, flags=[FlagFactory(level=FlagLevels.GOOD, team=self.team)]
        )
        self.good_2 = GoodFactory(organisation=self.organisation)

        role = Role(name="review_goods")
        role.permissions.set([constants.GovPermissions.REVIEW_GOODS.name])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        self.application = self.create_draft_standard_application(organisation=self.organisation)
        GoodOnApplication(good=self.good_1, application=self.application, quantity=10, unit=Units.NAR, value=500).save()
        GoodOnApplication(good=self.good_2, application=self.application, quantity=10, unit=Units.NAR, value=500).save()
        self.case = self.submit_application(self.application)
        self.url = reverse_lazy("goods:control_list_entries", kwargs={"case_pk": self.case.id})

    def test_verify_multiple_goods(self):
        """
        Post multiple goods to the endpoint, and check that the control code is updated for both
        """

        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": GoodControlled.YES,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        verified_good_1 = Good.objects.get(pk=self.good_1.pk)
        verified_good_2 = Good.objects.get(pk=self.good_2.pk)

        self.assertEqual(verified_good_1.control_list_entries.get().rating, "ML1a")
        self.assertEqual(verified_good_2.control_list_entries.get().rating, "ML1a")

    def test_verify_single_good_NLR(self):
        """
        Post a singular good to the endpoint, and check that the control code is not set if good is not controlled
        """
        data = {
            "objects": self.good_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": GoodControlled.NO,
            "control_list_entries": ["ML1a"],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.good_1.refresh_from_db()
        self.assertEqual(self.good_1.control_list_entries.count(), 0)

        # determine that flags have been removed when good verified
        self.assertEqual(self.good_1.flags.count(), 0)

    def test_verify_multiple_goods_NLR(self):
        """
        Post multiple goods to the endpoint, and check that the control code is not set if good is not controlled
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": GoodControlled.NO,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.good_1.refresh_from_db()
        self.good_2.refresh_from_db()
        self.assertEqual(self.good_1.control_list_entries.count(), 0)
        self.assertEqual(self.good_2.control_list_entries.count(), 0)

    def test_invalid_good_pk(self):
        """
        Post multiple goods to the endpoint, and test that 404 response, and that other good is updated
        """
        data = {
            "objects": [self.team.pk, self.good_1.pk],  # first value is invalid
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": GoodControlled.NO,
            "control_list_entries": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_list_entries.count(), 0)

    def test_standard_invalid_control_list_entries(self):
        """
        Post multiple goods to the endpoint, and that a bad request is returned, and that flags is not updated
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": GoodControlled.YES,
            "control_list_entries": ["invalid"],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an invalid control code, flags should not be removed
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertTrue(is_not_verified_flag_set_on_good(verified_good))

    def test_standard_controlled_good_empty_control_list_entries(self):
        """
        Post multiple goods, with an blank control_list_entries and is controlled, for a 400 response, and no update of goods
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": GoodControlled.YES,
            "control_list_entries": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an empty control code, flags should not be removed
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertTrue(is_not_verified_flag_set_on_good(verified_good))

    def test_user_cannot_review_good_without_permissions(self):
        """
        Tests that the right level of permissions are required by a gov user to review a good.
        """
        # create a second user to adopt the super user role as it will
        # overwritten otherwise if we try and remove the role from the first
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role
        )
        valid_user.save()

        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.post(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_cannot_set_control_list_entries_when_application_in_terminal_state(self, terminal_status):
        self.application.status = get_case_status_by_status(terminal_status)
        self.application.save()

        data = {
            "objects": self.good_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_list_entries": "ML1a",
            "is_good_controlled": "yes",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)


class GoodsVerifiedTestsOpenApplication(DataTestClient):
    def setUp(self):
        super().setUp()

        self.report_summary = self.create_picklist_item(
            "Report Summary", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE
        )

        role = Role(name="review_goods")
        role.permissions.set([constants.GovPermissions.REVIEW_GOODS.name])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        self.application = self.create_draft_open_application(organisation=self.organisation)

        self.good_1 = GoodsTypeFactory(application=self.application)
        self.good_1.flags.add(self.create_flag("New Flag", "Good", self.team))
        self.good_2 = GoodsTypeFactory(application=self.application)

        self.case = self.submit_application(self.application)
        self.url = reverse_lazy("goods:control_list_entries", kwargs={"case_pk": self.case.id})

    def test_verify_single_good(self):
        """
        Post a singular good to the endpoint, and check that the control code is updated, and flags are removed
        """
        data = {
            "objects": self.good_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": GoodControlled.YES,
            "control_list_entries": ["ML1a"],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.good_1.refresh_from_db()
        self.assertEqual(list(self.good_1.control_list_entries.values_list("rating", flat=True)), ["ML1a"])

        # determine that flags have been removed when good verified
        self.assertFalse(is_not_verified_flag_set_on_good(self.good_1))

    def test_verify_only_change_comment_doesnt_remove_flags(self):
        """
        Assert that not changing the control code does not remove the flags
        """
        self.good_1.is_good_controlled = "True"
        self.good_1.control_list_entries.set([get_control_list_entry("ML1a")])
        self.good_1.save()
        data = {
            "objects": self.good_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.good_1.refresh_from_db()
        self.assertEqual(list(self.good_1.control_list_entries.values_list("rating", flat=True)), ["ML1a"])

        # determine that flags have not been removed when control code hasn't changed
        self.assertEqual(self.good_1.flags.count(), 1)

    def test_invalid_control_list_entries(self):
        """
        Post multiple goods to the endpoint, and that a bad request is returned, and that flags are not updated
        """

        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_list_entries": ["invalid"],
            "is_good_controlled": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an invalid control code, flags should not be removed
        self.good_1.refresh_from_db()
        self.good_2.refresh_from_db()
        self.assertTrue(is_not_verified_flag_set_on_good(self.good_1))
        self.assertTrue(is_not_verified_flag_set_on_good(self.good_2))

    def test_user_cannot_review_goods_without_permissions(self):
        """
        Tests that the right level of permissions are required
        """
        # create a second user to adopt the super user role as it will
        # overwritten otherwise if we try and remove the role from the first
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role
        )
        valid_user.save()

        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.post(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
