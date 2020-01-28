from rest_framework import serializers
from rest_framework.fields import CharField

from applications.models import StandardApplication, ApplicationDocument
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from cases.enums import CaseTypeEnum
from lite_content.lite_api import strings
from parties.serializers import (
    EndUserSerializer,
    EndUserWithFlagsSerializer,
    UltimateEndUserWithFlagsSerializer,
    ThirdPartyWithFlagsSerializer,
    ConsigneeWithFlagsSerializer,
)


class StandardApplicationViewSerializer(GenericApplicationViewSerializer):
    end_user = EndUserWithFlagsSerializer()
    ultimate_end_users = UltimateEndUserWithFlagsSerializer(many=True)
    third_parties = ThirdPartyWithFlagsSerializer(many=True)
    consignee = ConsigneeWithFlagsSerializer()
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

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
            "destinations",
            "additional_documents",
        )

    def get_destinations(self, application):
        if application.end_user:
            serializer = EndUserSerializer(application.end_user)
            return {"type": "end_user", "data": serializer.data}
        else:
            return {"type": "end_user", "data": ""}

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance)
        return ApplicationDocumentSerializer(documents, many=True).data


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["type"] = CaseTypeEnum.APPLICATION

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
        error_messages={"blank": strings.Applications.REF_NAME},
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
