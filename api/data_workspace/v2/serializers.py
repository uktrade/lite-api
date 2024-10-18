from rest_framework import serializers

from api.cases.generated_documents.models import GeneratedCaseDocument
from api.licences.enums import LicenceStatus
from api.licences.models import Licence

SIEL_TEMPLATE_ID = "d159b195-9256-4a00-9bc8-1eb2cebfa1d2"


class LicenceSerializer(serializers.ModelSerializer):
    decision = serializers.SerializerMethodField()
    issued_date = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
            "decision",
            "issued_date",
        )

    def get_decision(self, licence):
        return LicenceStatus.ISSUED

    def get_issued_date(self, licence):
        licence_document = GeneratedCaseDocument.objects.filter(
            licence=licence,
            template_id=SIEL_TEMPLATE_ID,
            safe=True,
            visible_to_exporter=True,
        )

        if licence_document.count() > 1:
            return "Multiple licence documents"

        return licence_document.first().updated_at
