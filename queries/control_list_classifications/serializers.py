from rest_framework import serializers

from conf.helpers import str_to_bool
from conf.serializers import PrimaryKeyRelatedSerializerField, ControlListEntryField
from goods.enums import GoodStatus
from goods.serializers import FullGoodSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from picklists.models import PicklistItem
from queries.control_list_classifications.models import ControlListClassificationQuery
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum


class ControlListClassificationQuerySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(queryset=Organisation.objects.all(),
                                                    serializer=TinyOrganisationViewSerializer)
    good = FullGoodSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ControlListClassificationQuery
        fields = ['id', 'details', 'good', 'submitted_at', 'organisation']


class ControlListClassificationQueryResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ControlListClassificationQuery
        fields = []

    # pylint: disable = W0221
    def update(self, instance, validated_data):
        instance.status = get_case_status_from_status_enum(CaseStatusEnum.FINALISED)

        instance.save()
        return instance
