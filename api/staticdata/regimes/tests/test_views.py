from rest_framework import status
from rest_framework.reverse import reverse

from test_helpers.clients import DataTestClient

from ..enums import (
    RegimesEnum,
    RegimeSubsectionsEnum,
)
from ..models import (
    Regime,
    RegimeEntry,
    RegimeSubsection,
)

from .factories import (
    RegimeFactory,
    RegimeEntryFactory,
    RegimeSubsectionFactory,
)


class MTCREntriesTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.mtcr_regime = Regime.objects.get(pk=RegimesEnum.MTCR)
        self.mtcr_category_1_subsection = RegimeSubsection.objects.get(pk=RegimeSubsectionsEnum.MTCR_CATEGORY_1)
        self.mtcr_category_2_subsection = RegimeSubsection.objects.get(pk=RegimeSubsectionsEnum.MTCR_CATEGORY_2)

        # Clear out regime entries created by data migrations so we have a clean
        # slate to test against
        RegimeEntry.objects.all().delete()

    def test_view(self):
        non_mtcr_regime = RegimeFactory.create()
        non_mtcr_regime_subsection = RegimeSubsectionFactory.create(regime=non_mtcr_regime)
        RegimeEntryFactory.create(subsection=non_mtcr_regime_subsection)

        RegimeEntryFactory.create(
            id="5dd10250-3f51-4359-963b-2b05cbec20ae",
            name="Z",
            subsection=self.mtcr_category_1_subsection,
        )
        RegimeEntryFactory.create(
            id="9a1f90c2-844c-437f-9ea3-783bf226b060",
            name="A",
            subsection=self.mtcr_category_2_subsection,
        )

        url = reverse("staticdata:regimes:mtcr_entries")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "name": "A",
                    "pk": "9a1f90c2-844c-437f-9ea3-783bf226b060",
                    "subsection": {
                        "name": "MTCR Category 2",
                        "pk": "77b14423-f33c-45a5-a512-61ddd380cf06",
                        "regime": {
                            "name": "MTCR",
                            "pk": "b1c1f990-a7be-4bc8-9292-a8b5ea25c0dd",
                        },
                    },
                },
                {
                    "name": "Z",
                    "pk": "5dd10250-3f51-4359-963b-2b05cbec20ae",
                    "subsection": {
                        "name": "MTCR Category 1",
                        "pk": "e529df3d-d471-49be-94d7-7a4e5835df90",
                        "regime": {
                            "name": "MTCR",
                            "pk": "b1c1f990-a7be-4bc8-9292-a8b5ea25c0dd",
                        },
                    },
                },
            ],
        )


class WassenaarEntriesTests(DataTestClient):
    def setUp(self):
        super().setUp()

        self.wassenaar_regime = Regime.objects.get(pk=RegimesEnum.WASSENAAR)
        self.wassenaar_arrangement_subsection = RegimeSubsection.objects.get(
            pk=RegimeSubsectionsEnum.WASSENAAR_ARRANGEMENT
        )
        self.wassenaar_arrangement_sensitive_subsection = RegimeSubsection.objects.get(
            pk=RegimeSubsectionsEnum.WASSENAAR_ARRANGEMENT_SENSITIVE
        )
        self.wassenaar_arrangement_very_sensitive_subsection = RegimeSubsection.objects.get(
            pk=RegimeSubsectionsEnum.WASSENAAR_ARRANGEMENT_VERY_SENSITIVE
        )

        # Clear out regime entries created by data migrations so we have a clean
        # slate to test against
        RegimeEntry.objects.all().delete()

    def test_view(self):
        non_wassenaar_regime = RegimeFactory.create()
        non_wassenaar_regime_subsection = RegimeSubsectionFactory.create(regime=non_wassenaar_regime)
        RegimeEntryFactory.create(subsection=non_wassenaar_regime_subsection)

        RegimeEntryFactory.create(
            id="2b552cf7-cb5b-4ec4-a834-0eeb0a6af1ec",
            name="C",
            subsection=self.wassenaar_arrangement_very_sensitive_subsection,
        )
        RegimeEntryFactory.create(
            id="2817d81b-bf0d-454b-ae82-1e8aa7734833",
            name="B",
            subsection=self.wassenaar_arrangement_sensitive_subsection,
        )
        RegimeEntryFactory.create(
            id="2798b8b1-f771-4ad6-acbc-0e07f642c6d8",
            name="A",
            subsection=self.wassenaar_arrangement_subsection,
        )

        url = reverse("staticdata:regimes:wassenaar_entries")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            [
                {
                    "pk": "2798b8b1-f771-4ad6-acbc-0e07f642c6d8",
                    "name": "A",
                    "subsection": {
                        "pk": "a67b1acd-0578-4b83-af66-36ac56f00296",
                        "name": "Wassenaar Arrangement",
                        "regime": {"pk": "66e5fc8d-67c7-4a5a-9d11-2eb8dbc57f7d", "name": "WASSENAAR"},
                    },
                },
                {
                    "pk": "2817d81b-bf0d-454b-ae82-1e8aa7734833",
                    "name": "B",
                    "subsection": {
                        "pk": "3bafdc58-f994-4e44-9f89-b01a037b9676",
                        "name": "Wassenaar Arrangement Sensitive",
                        "regime": {"pk": "66e5fc8d-67c7-4a5a-9d11-2eb8dbc57f7d", "name": "WASSENAAR"},
                    },
                },
                {
                    "pk": "2b552cf7-cb5b-4ec4-a834-0eeb0a6af1ec",
                    "name": "C",
                    "subsection": {
                        "pk": "deb7099a-dfeb-47c7-9dce-d9228a8337e0",
                        "name": "Wassenaar Arrangement Very Sensitive",
                        "regime": {"pk": "66e5fc8d-67c7-4a5a-9d11-2eb8dbc57f7d", "name": "WASSENAAR"},
                    },
                },
            ],
        )
