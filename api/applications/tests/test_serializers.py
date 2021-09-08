from test_helpers.clients import DataTestClient

from api.goods.tests.factories import GoodFactory
from api.cases.enums import AdviceType
from api.applications.serializers.advice import AdviceCreateSerializer


class TestAdviceSerializer(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.good = GoodFactory(
            organisation=self.organisation, is_good_controlled=True, control_list_entries=["ML1a"],
        )

    def test_advice_serializer_good_field(self):
        data = [{
            "user": self.gov_user.baseuser_ptr.id,
            "good": self.good.id,
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }]
        serializer = AdviceCreateSerializer(data=data, many=True)

        assert serializer.is_valid()

    def test_advice_serializer_good_field_good_on_application(self):
        data = [{
            "user": self.gov_user.baseuser_ptr.id,
            "good": self.good_on_application.id,
            "text": "Text",
            "type": AdviceType.APPROVE,
            "level": "user",
            "team": self.team.id,
            "proviso": "",
            "denial_reasons": [],
            "note": "",
            "footnote": None,
            "footnote_required": "False",
            "case": self.case.id,
        }]
        serializer = AdviceCreateSerializer(data=data, many=True)

        assert serializer.is_valid()
