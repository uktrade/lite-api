from rest_framework import serializers

from applications.models import ApplicationDocument
from applications.models import ExhibitionClearanceApplication
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
)
from applications.serializers.good import GoodOnApplicationViewSerializer
from cases.enums import CaseTypeEnum
from parties.serializers import (
    EndUserSerializer,
    EndUserWithFlagsSerializer,
    UltimateEndUserWithFlagsSerializer,
    ThirdPartyWithFlagsSerializer,
    ConsigneeWithFlagsSerializer,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class ExhibitionClearanceViewSerializer(GenericApplicationViewSerializer):
    end_user = EndUserWithFlagsSerializer()
    ultimate_end_users = UltimateEndUserWithFlagsSerializer(many=True)
    third_parties = ThirdPartyWithFlagsSerializer(many=True)
    consignee = ConsigneeWithFlagsSerializer()
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = ExhibitionClearanceApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "goods",
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


class ExhibitionClearanceCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["organisation"] = self.context.id
        self.initial_data["type"] = CaseTypeEnum.EXHIBITION_CLEARANCE
        self.initial_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT).id

    class Meta:
        model = ExhibitionClearanceApplication
        fields = (
            "id",
            "name",
            "application_type",
            "organisation",
            "type",
            "status",
        )
