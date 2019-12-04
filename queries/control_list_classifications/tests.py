from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status

from audit_trail.models import Audit
from cases.models import Case
from conf.constants import Permissions
from goods.enums import GoodControlled, GoodStatus
from goods.models import Good
from picklists.enums import PicklistType, PickListStatus
from queries.control_list_classifications.models import ControlListClassificationQuery
from test_helpers.clients import DataTestClient
from users.models import Role, GovUser


class ControlListClassificationsQueryCreateTests(DataTestClient):

    url = reverse("queries:control_list_classifications:control_list_classifications")

    def test_create_control_list_classification_query(self):
        """
        Ensure that an exporter can raise a control list
        classification query and that a case has been created
        """
        good = Good(
            description="Good description",
            is_good_controlled=GoodControlled.UNSURE,
            control_code="ML1",
            is_good_end_product=True,
            part_number="123456",
            organisation=self.organisation,
        )
        good.save()

        data = {
            "good_id": good.id,
            "not_sure_details_control_code": "ML1a",
            "not_sure_details_details": "I don't know",
        }

        response = self.client.post(self.url, data, **self.exporter_headers)
        response_data = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_data["id"], ControlListClassificationQuery.objects.get().id)
        self.assertEqual(Case.objects.count(), 1)


class ControlListClassificationsQueryUpdateTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.report_summary = self.create_picklist_item(
            "Report Summary", self.team, PicklistType.REPORT_SUMMARY, PickListStatus.ACTIVE,
        )

        self.query = self.create_clc_query("This is a widget", self.organisation)

        role = Role(name="review_goods")
        role.permissions.set([Permissions.REVIEW_GOODS])
        role.save()
        self.gov_user.role = role
        self.gov_user.save()

        self.url = reverse(
            "queries:control_list_classifications:control_list_classification", kwargs={"pk": self.query.pk},
        )

    def test_respond_to_control_list_classification_query(self):
        """
        Ensure that a gov user can respond to a control list
        classification query with a control code
        """
        data = {
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "control_code": "ML1a",
            "is_good_controlled": "yes",
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.query.good.control_code, data["control_code"])
        self.assertEqual(self.query.good.is_good_controlled, str(data["is_good_controlled"]))
        self.assertEqual(self.query.good.status, GoodStatus.VERIFIED)

        # Check that an audit item has been added
        qs = Audit.objects.filter(
            target_object_id=self.query.case.get().id,
            target_content_type=ContentType.objects.get_for_model(self.query.case.get())
        )
        self.assertEqual(qs.count(), 1)

    def test_respond_to_control_list_classification_query_nlr(self):
        """
        Ensure that a gov user can respond to a control list
        classification query with no licence required
        """
        data = {
            "comment": "I Am Easy to Find",
            "report_summary": self.report_summary.pk,
            "is_good_controlled": "no",
        }

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.query.good.control_code, "")
        self.assertEqual(self.query.good.is_good_controlled, str(data["is_good_controlled"]))
        self.assertEqual(self.query.good.status, GoodStatus.VERIFIED)

        # Check that an activity item has been added
        qs = Audit.objects.filter(
            target_object_id=self.query.case.get().id,
            target_content_type=ContentType.objects.get_for_model(self.query.case.get())
        )
        self.assertEqual(qs.count(), 1)

    def test_respond_to_control_list_classification_query_failure(self):
        """
        Ensure that a gov user cannot respond to a control list
        classification query without providing data
        """
        data = {}

        response = self.client.put(self.url, data, **self.gov_headers)
        self.query.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.query.good.status, GoodStatus.DRAFT)

    # User must have permission to create team advice
    def test_user_cannot_respond_to_clc_without_permissions(self):
        """
        Tests that the right level of permissions are required
        """
        # Make sure at least one user maintains the super user role
        valid_user = GovUser(
            email="test2@mail.com", first_name="John", last_name="Smith", team=self.team, role=self.super_user_role,
        )
        valid_user.save()

        self.gov_user.role = self.default_role
        self.gov_user.save()

        response = self.client.put(self.url, **self.gov_headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
