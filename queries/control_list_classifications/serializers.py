from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField
from goods.serializers import GoodWithFlagsSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from queries.control_list_classifications.models import ControlListClassificationQuery
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


class ControlListClassificationQuerySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=TinyOrganisationViewSerializer
    )
    good = GoodWithFlagsSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ControlListClassificationQuery
        fields = ("id", "details", "good", "submitted_at", "organisation", "status")

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None
