from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import HmrcQuery, ApplicationDocument
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import GenericApplicationViewSerializer
from cases.enums import CaseTypeEnum
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from organisations.enums import OrganisationType
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from parties.serializers import (
    EndUserSerializer,
    UltimateEndUserSerializer,
    ThirdPartySerializer,
    ConsigneeSerializer,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class HmrcQueryViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    end_user = EndUserSerializer()
    ultimate_end_users = UltimateEndUserSerializer(many=True)
    third_parties = ThirdPartySerializer(many=True)
    consignee = ConsigneeSerializer()
    hmrc_organisation = TinyOrganisationViewSerializer()
    supporting_documentation = serializers.SerializerMethodField()

    class Meta:
        model = HmrcQuery
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "goods_types",
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "hmrc_organisation",
            "reasoning",
            "supporting_documentation",
            "have_goods_departed",
        )

    def get_goods_types(self, instance):
        goods_types = GoodsType.objects.filter(application=instance)
        return FullGoodsTypeSerializer(goods_types, many=True).data

    def get_supporting_documentation(self, application):
        documents = ApplicationDocument.objects.filter(application=application)
        return ApplicationDocumentSerializer(documents, many=True).data


class HmrcQueryCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    hmrc_organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.context.type != OrganisationType.HMRC:
            raise exceptions.PermissionDenied("User does not belong to an HMRC organisation")

        self.initial_data["hmrc_organisation"] = self.context.id
        self.initial_data["type"] = CaseTypeEnum.HMRC_QUERY
        self.initial_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT).id

    class Meta:
        model = HmrcQuery
        fields = (
            "reasoning",
            "application_type",
            "organisation",
            "hmrc_organisation",
            "type",
            "status",
        )


class HmrcQueryUpdateSerializer(serializers.ModelSerializer):
    reasoning = serializers.CharField(max_length=1000, allow_null=True, allow_blank=True)

    class Meta:
        model = HmrcQuery
        fields = (
            "reasoning",
            "status",
            "have_goods_departed",
        )
