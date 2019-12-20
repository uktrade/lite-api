from rest_framework import serializers
from rest_framework.fields import CharField

from applications.models import OpenApplication, ApplicationDocument
from applications.serializers.document import ApplicationDocumentSerializer
from applications.serializers.generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationUpdateSerializer,
    GenericApplicationViewSerializer,
)
from cases.enums import CaseTypeEnum
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from lite_content.lite_api import strings
from static.countries.models import Country
from static.countries.serializers import CountryWithFlagsSerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class OpenApplicationViewSerializer(GenericApplicationViewSerializer):
    goods_types = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = GenericApplicationViewSerializer.Meta.fields + (
            "activity",
            "usage",
            "goods_types",
            "destinations",
            "additional_documents",
        )

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        serializer = FullGoodsTypeSerializer(goods_types, many=True)
        return serializer.data

    def get_destinations(self, application):
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountryWithFlagsSerializer(countries, many=True)
        return {"type": "countries", "data": serializer.data}

    def get_additional_documents(self, instance):
        documents = ApplicationDocument.objects.filter(application=instance)
        return ApplicationDocumentSerializer(documents, many=True).data


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["organisation"] = self.context.id
        self.initial_data["type"] = CaseTypeEnum.APPLICATION
        self.initial_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT).id

    class Meta:
        model = OpenApplication
        fields = (
            "id",
            "name",
            "application_type",
            "export_type",
            "organisation",
            "type",
            "status",
        )


class OpenApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": strings.Goods.REF_NAME},
    )

    class Meta:
        model = OpenApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
