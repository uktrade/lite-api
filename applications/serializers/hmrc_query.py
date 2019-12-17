from django.db.models import Count
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import HmrcQuery, ApplicationDocument
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import GenericApplicationListSerializer
from cases.enums import CaseTypeEnum
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from organisations.enums import OrganisationType
from organisations.models import Organisation, Site, ExternalLocation
from organisations.serializers import (
    TinyOrganisationViewSerializer,
    SiteViewSerializer,
    ExternalLocationSerializer,
)
from parties.serializers import (
    EndUserSerializer,
    UltimateEndUserSerializer,
    ThirdPartySerializer,
    ConsigneeSerializer,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import ExporterNotification


class HmrcQueryViewSerializer(GenericApplicationListSerializer):
    goods_types = serializers.SerializerMethodField()
    end_user = EndUserSerializer()
    ultimate_end_users = UltimateEndUserSerializer(many=True)
    third_parties = ThirdPartySerializer(many=True)
    consignee = ConsigneeSerializer()
    hmrc_organisation = TinyOrganisationViewSerializer()
    goods_locations = serializers.SerializerMethodField()
    supporting_documentation = serializers.SerializerMethodField()

    def get_goods_types(self, instance):
        goods_types = GoodsType.objects.filter(application=instance)
        return FullGoodsTypeSerializer(goods_types, many=True).data

    def get_goods_locations(self, application):
        sites = Site.objects.filter(sites_on_application__application=application)

        if sites:
            serializer = SiteViewSerializer(sites, many=True)
            return {"type": "sites", "data": serializer.data}

        external_locations = ExternalLocation.objects.filter(external_locations_on_application__application=application)

        if external_locations:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {"type": "external_locations", "data": serializer.data}

        return {}

    def get_supporting_documentation(self, application):
        documents = ApplicationDocument.objects.filter(application=application)
        return ApplicationDocumentSerializer(documents, many=True).data

    def get_exporter_user_notifications_count(self, instance):
        """
        Overriding parent class
        """

        # TODO: LT-1443 Refactor into helper method
        exporter_user = self.context.get("exporter_user")
        if exporter_user:
            count_queryset = (
                ExporterNotification.objects.filter(
                    user=exporter_user, organisation=exporter_user.organisation, case=instance
                )
                .values("content_type__model")
                .annotate(count=Count("content_type__model"))
            )

            user_notifications_total_count = 0
            user_notifications_count = {}
            for content_type in count_queryset:
                user_notifications_count[content_type["content_type__model"]] = content_type["count"]
                user_notifications_total_count += content_type["count"]
            user_notifications_count["total"] = user_notifications_total_count

            return user_notifications_count
        else:
            return None

    class Meta:
        model = HmrcQuery
        fields = GenericApplicationListSerializer.Meta.fields + (
            "goods_types",
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "hmrc_organisation",
            "reasoning",
            "goods_locations",
            "supporting_documentation",
        )


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
        )
