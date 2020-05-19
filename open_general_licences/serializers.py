from rest_framework import serializers

from cases.models import CaseType
from conf.serializers import ControlListEntryField
from open_general_licences.models import OpenGeneralLicence
from static.countries.models import Country


class OpenGeneralLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    description = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    url = serializers.URLField(required=True, allow_blank=False, allow_null=False, )
    case_type = serializers.PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(), required=True, allow_null=False, allow_empty=False
    )
    countries = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), many=True, required=True, allow_null=False, allow_empty=False
    )
    control_list_entries = ControlListEntryField(many=True, required=True, allow_empty=True)

    class Meta:
        model = OpenGeneralLicence
        fields = "__all__"

    def validate_url(self, url):
        if "gov.uk" not in url.lower():
            raise serializers.ValidationError("Has to be on the gov uk domain")

        return url
