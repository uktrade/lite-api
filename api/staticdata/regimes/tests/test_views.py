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

        mtcr_regimes = [
            RegimeEntryFactory.create(name="Z", subsection=self.mtcr_category_1_subsection),
            RegimeEntryFactory.create(name="A", subsection=self.mtcr_category_2_subsection),
        ]

        url = reverse("staticdata:regimes:mtcr_entries")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {"entries": [[str(r.pk), r.name] for r in sorted(mtcr_regimes, key=lambda r: r.name)]},
        )
