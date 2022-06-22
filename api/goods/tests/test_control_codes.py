from django.urls import reverse_lazy, reverse
from parameterized import parameterized
from rest_framework import status

from api.flags.enums import SystemFlags
from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.applications.models import GoodOnApplication
from api.applications.tests.factories import GoodOnApplicationFactory
from api.core import constants
from api.flags.enums import FlagLevels
from api.flags.tests.factories import FlagFactory
from api.goods.models import Good
from api.goods.tests.factories import GoodFactory
from api.goodstype.tests.factories import GoodsTypeFactory
from api.picklists.enums import PicklistType, PickListStatus
from api.staticdata.control_list_entries.helpers import get_control_list_entry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.units.enums import Units
from api.users.tests.factories import GovUserFactory
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
        self.good_on_application_1 = GoodOnApplication.objects.create(
            good=self.good_1, application=self.application, quantity=10, unit=Units.NAR, value=500
        )
        self.good_on_application_2 = GoodOnApplication.objects.create(
            good=self.good_2, application=self.application, quantity=10, unit=Units.NAR, value=500
        )
        self.case = self.submit_application(self.application)
        self.url = reverse_lazy("goods:control_list_entries", kwargs={"case_pk": self.case.id})

    def test_verify_multiple_goods(self):
        """
        Post multiple goods to the endpoint, and check that the control code is updated for both
        """

        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": True,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        verified_good_1 = Good.objects.get(pk=self.good_1.pk)
        verified_good_2 = Good.objects.get(pk=self.good_2.pk)

        self.assertEqual(verified_good_1.control_list_entries.get().rating, "ML1a")
        self.assertEqual(verified_good_2.control_list_entries.get().rating, "ML1a")

    def test_report_summary_saved_goodonapplication(self):
        """
        Make sure report_summary is saved to the GoodOnApplication
        """

        data = {
            "objects": [self.good_1.pk],
            "current_object": self.good_on_application_1.pk,
            "control_list_entries": ["ML1a"],
            "is_precedent": False,
            "is_good_controlled": True,
            "end_use_control": [],
            "report_summary": self.report_summary.text,
            "comment": "Lorem ipsum",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.good_on_application_1.refresh_from_db()

        self.assertEqual(self.good_on_application_1.report_summary, self.report_summary.text)

    def test_verify_multiple_goods_NLR(self):
        """
        Post multiple goods to the endpoint, and check that the control code is not set if good is not controlled
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": False,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.good_1.refresh_from_db()
        self.good_2.refresh_from_db()
        self.assertEqual(self.good_1.control_list_entries.count(), 1)
        self.assertEqual(self.good_2.control_list_entries.count(), 1)

    def test_invalid_good_pk(self):
        # given one of the good pk is invalid
        data = {
            "objects": [self.team.pk, self.good_1.pk],
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "is_good_controlled": False,
            "control_list_entries": ["ML1b"],
        }

        # when I review the goods
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        # then the valid good is updated
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertEqual(verified_good.control_list_entries.count(), 1)

    @parameterized.expand(
        [
            (
                # legacy where frontend doesn't send is_precedent
                {
                    "comment": "I Am Easy to Find",
                    "is_good_controlled": False,
                    "control_list_entries": [],
                },
                False,
            ),
            (
                # precedent = False
                {
                    "comment": "I Am Easy to Find",
                    "is_good_controlled": False,
                    "control_list_entries": [],
                    "is_precedent": False,
                },
                False,
            ),
            (
                # precedent = True
                {
                    "comment": "I Am Easy to Find",
                    "is_good_controlled": False,
                    "control_list_entries": [],
                    "is_precedent": True,
                },
                True,
            ),
        ]
    )
    def test_is_precedent_is_set(self, input, expected_is_precedent):
        defaults = {
            "objects": [self.good_1.pk],
            "current_object": self.good_on_application_1.pk,
            "report_summary": self.report_summary.text,
        }
        data = {**defaults, **input}

        # when I review the goods
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

        # then the good_on_application is updated
        verified_good_on_application = GoodOnApplication.objects.get(pk=self.good_on_application_1.pk)
        self.assertEqual(verified_good_on_application.is_precedent, expected_is_precedent)

    def test_standard_invalid_control_list_entries(self):
        """
        Post multiple goods to the endpoint, and that a bad request is returned, and that flags is not updated
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "is_good_controlled": True,
            "control_list_entries": ["invalid"],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # since it has an invalid control code, flags should not be removed
        verified_good = Good.objects.get(pk=self.good_1.pk)
        self.assertTrue(is_not_verified_flag_set_on_good(verified_good))

    def test_standard_controlled_good_empty_control_list_entries(self):
        """
        Post multiple goods, with an blank control_list_entries and is controlled, for a 400 response, and no update of goods
        """
        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "is_good_controlled": True,
            "control_list_entries": [],
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_review_good_without_permissions(self):
        """
        Tests that the right level of permissions are required by a gov user to review a good.
        """
        # create a second user to adopt the super user role as it will
        # overwritten otherwise if we try and remove the role from the first
        valid_user = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team,
            role=self.super_user_role,
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
            "current_object": self.good_on_application_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "control_list_entries": "ML1a",
            "is_good_controlled": "yes",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_report_summary_updates_same_product_added_twice(self):
        self.product_on_application1 = GoodOnApplication.objects.create(
            good=self.good_1,
            application=self.application,
            quantity=10,
            unit=Units.NAR,
            value=500,
            report_summary="Rifles (10)",
        )
        self.product_on_application2 = GoodOnApplication.objects.create(
            good=self.good_1,
            application=self.application,
            quantity=5,
            unit=Units.NAR,
            value=500,
            report_summary="Rifles (5)",
        )
        data = {
            "objects": [self.good_1.pk],
            "current_object": self.product_on_application1.pk,
            "control_list_entries": ["ML1a"],
            "is_precedent": False,
            "is_good_controlled": True,
            "end_use_control": [],
            "report_summary": "Sniper rifles (10)",
            "comment": "report summary update test",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product_on_application1.refresh_from_db()

        self.assertEqual(self.product_on_application1.report_summary, "Sniper rifles (10)")
        self.assertEqual(self.product_on_application2.report_summary, "Rifles (5)")
        audit_qs = Audit.objects.filter(verb=AuditType.PRODUCT_REVIEWED)
        self.assertEqual(audit_qs.count(), 3)
        # because we added the same product twice check if reviewing the second has not modified
        # first product report summary value
        product1_audit = [item for item in audit_qs if item.action_object.id == self.product_on_application1.id]
        audit_payload = product1_audit[0].payload
        self.assertEqual(audit_payload["old_report_summary"], "Rifles (10)")
        self.assertEqual(audit_payload["report_summary"], "Sniper rifles (10)")


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

    def test_invalid_control_list_entries(self):
        """
        Post multiple goods to the endpoint, and that a bad request is returned, and that flags are not updated
        """

        data = {
            "objects": [self.good_1.pk, self.good_2.pk],
            "current_object": self.good_1.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "control_list_entries": ["invalid"],
            "is_good_controlled": "True",
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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
        valid_user = GovUserFactory(
            baseuser_ptr__email="test2@mail.com",
            baseuser_ptr__first_name="John",
            baseuser_ptr__last_name="Smith",
            team=self.team,
            role=self.super_user_role,
        )
        valid_user.save()

        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.post(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WASSENAARFlagTest(DataTestClient):
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

        self.application = self.create_draft_standard_application(organisation=self.organisation)

        self.good = GoodOnApplicationFactory(
            application=self.application,
            good=GoodFactory(organisation=self.organisation),
        )

        self.case = self.submit_application(self.application)
        self.url = reverse("goods:control_list_entries", kwargs={"case_pk": self.case.id})

    def test_wassenaar_flags(self):
        """
        Assert that is_wassenaar field sets the wassenaar flag
        """

        # Add WASSENAAR flag
        data = {
            "objects": self.good.good.pk,
            "current_object": self.good.pk,
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.text,
            "control_list_entries": ["ML1a"],
            "is_good_controlled": True,
            "is_wassenaar": True,
        }

        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.good.refresh_from_db()
        assert self.good.good.flags.filter(id=SystemFlags.WASSENAAR).exists()

        # Remove WASSENAAR flag
        data["is_wassenaar"] = False
        response = self.client.post(self.url, data, **self.gov_headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.good.refresh_from_db()
        assert not self.good.good.flags.filter(id=SystemFlags.WASSENAAR).exists()
