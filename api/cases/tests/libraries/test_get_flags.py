from collections import OrderedDict

from test_helpers.clients import DataTestClient

from api.applications.tests.factories import (
    GoodOnApplicationFactory,
    PartyOnApplicationFactory,
    StandardApplicationFactory,
)
from api.cases.libraries.get_flags import (
    get_flags,
    get_ordered_flags,
)
from api.flags.enums import FlagLevels
from api.flags.tests.factories import FlagFactory
from api.goods.tests.factories import FirearmFactory, GoodFactory


class TestGetFlags(DataTestClient):
    def setUp(self):
        super().setUp()

        self.application = StandardApplicationFactory(
            organisation=self.organisation,
        )

    def test_no_flags(self):
        flags = get_flags(self.application)
        self.assertQuerysetEqual(flags, [])

    def test_goods_flags(self):
        good = GoodFactory(
            organisation=self.organisation,
        )
        firearm_details = FirearmFactory()
        GoodOnApplicationFactory(
            application=self.application,
            firearm_details=firearm_details,
            good=good,
        )
        flag = FlagFactory(level=FlagLevels.GOOD, team=self.team)
        good.flags.add(flag)
        flags = get_flags(self.application)
        self.assertQuerysetEqual(flags, [flag])

    def test_destination_flags(self):
        flag = FlagFactory(level=FlagLevels.PARTY_ON_APPLICATION, team=self.team)
        party_on_application = PartyOnApplicationFactory(application=self.application)
        party_on_application.party.flags.add(flag)
        flags = get_flags(self.application)
        self.assertQuerysetEqual(flags, [flag])

    def test_case_flags(self):
        flag = FlagFactory(level=FlagLevels.PARTY_ON_APPLICATION, team=self.team)
        self.application.flags.add(flag)
        flags = get_flags(self.application)
        self.assertQuerysetEqual(flags, [flag])

    def test_organisation_flags(self):
        flag = FlagFactory(level=FlagLevels.PARTY_ON_APPLICATION, team=self.team)
        self.organisation.flags.add(flag)
        flags = get_flags(self.application)
        self.assertQuerysetEqual(flags, [flag])


class TestGetOrderedFlags(DataTestClient):
    def test_deduplication_of_flags(self):
        application = StandardApplicationFactory(
            organisation=self.organisation,
        )
        goods = [
            GoodFactory(
                organisation=self.organisation,
            ),
            GoodFactory(
                organisation=self.organisation,
            ),
        ]
        flag = FlagFactory(level=FlagLevels.GOOD, team=self.team)
        for good in goods:
            firearm_details = FirearmFactory()
            GoodOnApplicationFactory(
                application=application,
                firearm_details=firearm_details,
                good=good,
            )
            good.flags.add(flag)
        flags = get_ordered_flags(application, self.team, distinct=True)
        self.assertEqual(
            [
                {
                    "id": str(flag.pk),
                    "name": flag.name,
                    "alias": flag.alias,
                    "label": flag.label,
                    "colour": flag.colour,
                    "priority": flag.priority,
                    "level": flag.level,
                }
            ],
            flags,
        )
