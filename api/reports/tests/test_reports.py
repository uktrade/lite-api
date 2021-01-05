import itertools
from datetime import datetime

from django.db import connection
from django.urls import reverse
from rest_framework import status

from api.cases.models import Case
from api.reports.queries.standard import GOODS_AND_RATINGS
from api.staticdata.control_list_entries.models import ControlListEntry
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient


class StandardReportTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_draft_standard_application(self.organisation)
        self.url = reverse("applications:application_submit", kwargs={"pk": self.draft.id})
        self.exporter_user.set_role(self.organisation, self.exporter_super_user_role)
        self.start_date = datetime(year=2000, month=1, day=1)
        self.end_date = datetime(year=2100, month=1, day=1)

    def execute_query(self, sql_query, start_date, end_date):
        with connection.cursor() as cursor:
            cursor.execute(sql_query, {"start_date": start_date, "end_date": end_date})
            desc = cursor.description
            headers = [x.name for x in desc]
            rows = cursor.fetchall()
            return headers, rows

    def test_draft_application_not_included_in_standard_applications_query(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})

        response = self.client.put(url, **self.exporter_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        case = Case.objects.get(id=draft.id)
        self.assertIsNone(case.submitted_at)
        self.assertEqual(case.status.status, CaseStatusEnum.DRAFT)

        application_query = GOODS_AND_RATINGS["applications"]
        _, rows = self.execute_query(application_query, self.start_date, self.end_date)
        self.assertTrue(len(rows) == 0)

    def test_non_draft_application_included_in_standard_applications_query(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})
        _ = self.client.put(url, **self.exporter_headers)
        draft.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        draft.save()

        application_query = GOODS_AND_RATINGS["applications"]
        _, rows = self.execute_query(application_query, self.start_date, self.end_date)
        self.assertEqual(len(rows), 1)

    def test_good_control_list_entries_good_rating_on_good(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})
        _ = self.client.put(url, **self.exporter_headers)
        draft.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        draft.save()

        application_query = GOODS_AND_RATINGS["goods_control_list_entries"]
        headers, rows = self.execute_query(application_query, self.start_date, self.end_date)
        self.assertEqual(len(rows), draft.goods.all().count())
        ratings_row_index = headers.index("ratings")
        ratings = set(itertools.chain.from_iterable([x[ratings_row_index].split(",") for x in rows]))
        goods = draft.goods.all()
        good_ratings = set()
        for good in goods:
            good_ratings.update(good.get_control_list_entries().values_list("rating", flat=True))

        self.assertSetEqual(ratings, good_ratings)

    def test_good_control_list_entries_good_rating_on_good_on_application(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})
        _ = self.client.put(url, **self.exporter_headers)
        draft.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        draft.save()

        goods = draft.goods.all()
        good_ratings = set()
        for good in goods:
            good.is_good_controlled = True
            good.control_list_entries.add(ControlListEntry.objects.get(rating="ML2a"))
            good.control_list_entries.add(ControlListEntry.objects.get(rating="ML13c"))
            good.save()
            good_ratings.update(good.get_control_list_entries().values_list("rating", flat=True))

        application_query = GOODS_AND_RATINGS["goods_control_list_entries"]
        headers, rows = self.execute_query(application_query, self.start_date, self.end_date)
        self.assertEqual(len(rows), draft.goods.all().count())
        ratings_row_index = headers.index("ratings")
        ratings = set(itertools.chain.from_iterable([x[ratings_row_index].split(",") for x in rows]))

        self.assertSetEqual(ratings, good_ratings)

    def test_good_control_list_entries_good_rating_on_good_on_application_and_on_good(self):
        draft = self.create_standard_application_with_incorporated_good(self.organisation)
        url = reverse("applications:application_submit", kwargs={"pk": draft.id})
        _ = self.client.put(url, **self.exporter_headers)
        draft.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        draft.save()

        good = draft.goods.first()
        good.is_good_controlled = True
        good.control_list_entries.add(ControlListEntry.objects.get(rating="ML2a"))
        good.save()

        good_ratings = set()
        for good in draft.goods.all():
            good_ratings.update(good.get_control_list_entries().values_list("rating", flat=True))

        application_query = GOODS_AND_RATINGS["goods_control_list_entries"]
        headers, rows = self.execute_query(application_query, self.start_date, self.end_date)
        self.assertEqual(len(rows), draft.goods.all().count())
        ratings_row_index = headers.index("ratings")
        ratings = set(itertools.chain.from_iterable([x[ratings_row_index].split(",") for x in rows]))

        self.assertSetEqual(ratings, good_ratings)
