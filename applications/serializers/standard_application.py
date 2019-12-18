from lite_content.lite_api import strings
from rest_framework.fields import CharField

from applications.models import StandardApplication
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationWithFlagsViewSerializer
from cases.enums import CaseTypeEnum
from parties.serializers import (
    EndUserSerializer,
    UltimateEndUserSerializer,
    ThirdPartySerializer,
    ConsigneeSerializer,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class StandardApplicationViewSerializer(GenericApplicationViewSerializer):
    end_user = EndUserSerializer()
    ultimate_end_users = UltimateEndUserSerializer(many=True)
    third_parties = ThirdPartySerializer(many=True)
    consignee = ConsigneeSerializer()
    goods = GoodOnApplicationWithFlagsViewSerializer(many=True, read_only=True)

    class Meta:
        model = StandardApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "goods",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "activity",
            "usage",
        )

    def get_destinations(self, application):
        if application.end_user:
            serializer = EndUserSerializer(application.end_user)
            return {"type": "end_user", "data": serializer.data}
        else:
            return {"type": "end_user", "data": ""}


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["organisation"] = self.context.id
        self.initial_data["type"] = CaseTypeEnum.APPLICATION
        self.initial_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT).id

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "name",
            "application_type",
            "export_type",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "organisation",
            "type",
            "status",
        )


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Goods.REF_NAME},
    )
    reference_number_on_information_form = CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + (
            "have_you_been_informed",
            "reference_number_on_information_form",
        )

    def update(self, instance, validated_data):
        instance.have_you_been_informed = validated_data.get("have_you_been_informed", instance.have_you_been_informed)
        if instance.have_you_been_informed == "yes":
            instance.reference_number_on_information_form = validated_data.get(
                "reference_number_on_information_form", instance.reference_number_on_information_form,
            )
        else:
            instance.reference_number_on_information_form = None
        instance = super().update(instance, validated_data)
        return instance
