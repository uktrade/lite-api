from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.applications.models import HmrcQuery, ApplicationDocument
from api.applications.serializers.document import ApplicationDocumentSerializer
from api.applications.serializers.generic_application import GenericApplicationViewSerializer
from cases.models import CaseType
from api.goodstype.models import GoodsType
from api.goodstype.serializers import GoodsTypeViewSerializer
from lite_content.lite_api import strings
from api.organisations.enums import OrganisationType
from api.organisations.models import Organisation
from api.organisations.serializers import TinyOrganisationViewSerializer
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.libraries.get_case_status import get_case_status_by_status


class HmrcQueryViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    hmrc_organisation = TinyOrganisationViewSerializer()
    supporting_documentation = serializers.SerializerMethodField()

    class Meta:
        model = HmrcQuery
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + ("goods_types", "hmrc_organisation", "reasoning", "supporting_documentation", "have_goods_departed",)
        )

    def get_goods_types(self, instance):
        goods_types = GoodsType.objects.filter(application=instance)
        return GoodsTypeViewSerializer(goods_types, many=True).data

    def get_supporting_documentation(self, application):
        documents = ApplicationDocument.objects.filter(application=application)
        return ApplicationDocumentSerializer(documents, many=True).data


class HmrcQueryCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    hmrc_organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    case_type = PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(), error_messages={"required": strings.Applications.Generic.NO_LICENCE_TYPE},
    )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)

        if self.context.type != OrganisationType.HMRC:
            raise exceptions.PermissionDenied("User does not belong to an HMRC organisation")

        self.initial_data["case_type"] = case_type_id
        self.initial_data["hmrc_organisation"] = self.context.id
        self.initial_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT).id

    class Meta:
        model = HmrcQuery
        fields = (
            "name",
            "reasoning",
            "case_type",
            "organisation",
            "hmrc_organisation",
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
