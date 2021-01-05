from api.licences.enums import LicenceStatus
from api.licences.models import GoodOnLicence, Licence
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer

from rest_framework import serializers


class GoodOnLicenceSerializer(serializers.ModelSerializer):
    control_list_entries = serializers.SerializerMethodField()
    is_good_controlled = serializers.SerializerMethodField()
    description = serializers.CharField(source="good.good.description")

    # instance.good is good_on_application
    # instance.good.good is canonical good
    def get_is_good_controlled(self, instance):
        if instance.good.is_good_controlled is None:
            return instance.good.good.is_good_controlled
        return instance.good.is_good_controlled

    def get_control_list_entries(self, instance):
        control_list_entries = instance.good.get_control_list_entries()
        return ControlListEntrySerializer(control_list_entries, many=True).data

    class Meta:
        model = GoodOnLicence
        fields = (
            "control_list_entries",
            "is_good_controlled",
            "description",
            "quantity",
            "usage",
        )


class LicenceSerializer(serializers.ModelSerializer):

    goods = GoodOnLicenceSerializer(many=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
            "status",
            "goods",
        )

    def get_status(self, instance):
        return LicenceStatus.to_str(instance.status)


def get_case_licences(case):
    licences = (
        Licence.objects.prefetch_related(
            "goods", "goods__good", "goods__good__good", "goods__good__good__control_list_entries"
        )
        .filter(case=case)
        .order_by("created_at")
    )
    return LicenceSerializer(licences, many=True).data
