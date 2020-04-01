from rest_framework import serializers

from applications.enums import LicenceDuration
from applications.models import BaseApplication, GoodOnApplication, PartyOnApplication
from cases.generated_documents.models import GeneratedCaseDocument
from conf.serializers import CountrySerializerField
from goods.models import Good
from licences.models import Licence
from lite_content.lite_api import strings
from parties.models import Party
from static.statuses.serializers import CaseStatusSerializer


class LicenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "application",
            "start_date",
            "duration",
            "is_complete",
        )

    def validate(self, data):
        """
        Check that the duration is valid
        """
        super().validate(data)
        if data.get("duration") and (
            data["duration"] > LicenceDuration.MAX.value or data["duration"] < LicenceDuration.MIN.value
        ):
            raise serializers.ValidationError(strings.Applications.Finalise.Error.DURATION_RANGE)
        return data


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "start_date",
            "duration",
            "is_complete",
        )


class GoodLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = (
            "description",
            "control_code",
        )


class GoodOnLicenceListSerializer(serializers.ModelSerializer):
    good = GoodLicenceListSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = (
            "good",
            "quantity",
        )


class DestinationLicenceListSerializer(serializers.ModelSerializer):
    class PartyLicenceSerializer(serializers.ModelSerializer):
        country = CountrySerializerField()

        class Meta:
            model = Party
            fields = ("name", "country")

    party = PartyLicenceSerializer()

    class Meta:
        model = PartyOnApplication
        fields = ("party",)


class DocumentLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "advice_type",
            "id",
        )


class ApplicationLicenceListSerializer(serializers.ModelSerializer):
    goods = GoodOnLicenceListSerializer(many=True, read_only=True)
    end_user = DestinationLicenceListSerializer()
    status = CaseStatusSerializer()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = ("reference_code", "end_user", "goods", "status", "documents")

    def get_documents(self, instance):
        documents = GeneratedCaseDocument.objects.filter(case=instance, advice_type__isnull=False)
        return DocumentLicenceListSerializer(documents, many=True).data


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer()

    class Meta:
        model = Licence
        fields = ("application",)
