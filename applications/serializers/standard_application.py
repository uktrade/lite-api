from django.db.models import Count

from lite_content.lite_api import strings
from rest_framework import serializers
from rest_framework.fields import CharField

from applications.models import StandardApplication, ApplicationDocument
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationListSerializer,
)
from applications.serializers.good import GoodOnApplicationWithFlagsViewSerializer
from cases.enums import CaseTypeEnum
from organisations.models import ExternalLocation, Site
from organisations.serializers import ExternalLocationSerializer, SiteViewSerializer
from parties.serializers import (
    EndUserSerializer,
    UltimateEndUserSerializer,
    ThirdPartySerializer,
    ConsigneeSerializer,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status
from users.models import ExporterNotification


class StandardApplicationViewSerializer(GenericApplicationListSerializer):
    end_user = EndUserSerializer()
    ultimate_end_users = UltimateEndUserSerializer(many=True)
    third_parties = ThirdPartySerializer(many=True)
    consignee = ConsigneeSerializer()
    goods = GoodOnApplicationWithFlagsViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    goods_locations = serializers.SerializerMethodField()
    # TODO: Rename to supporting_documentation when possible
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        fields = GenericApplicationListSerializer.Meta.fields + (
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "goods",
            "destinations",
            "have_you_been_informed",
            "reference_number_on_information_form",
            "goods_locations",
            "activity",
            "usage",
            "additional_documents",
        )

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

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance)
        return ApplicationDocumentSerializer(documents, many=True).data

    def get_destinations(self, application):
        if application.end_user:
            serializer = EndUserSerializer(application.end_user)
            return {"type": "end_user", "data": serializer.data}
        else:
            return {"type": "end_user", "data": ""}

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
        error_messages={"blank": strings.Goods.ErrorMessages.REF_NAME},
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
