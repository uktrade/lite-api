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
        fields = ['id', 'details', 'good', 'submitted_at', 'organisation',
                  'comment', 'report_summary']


class ControlListClassificationQueryResponseSerializer(serializers.ModelSerializer):
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    is_good_controlled = serializers.BooleanField(allow_null=False, required=True, write_only=True)
    comment = serializers.CharField(allow_blank=False, max_length=500, required=True)
    report_summary = serializers.PrimaryKeyRelatedField(queryset=PicklistItem.objects.all(),
                                                        required=True,
                                                        allow_null=False,
                                                        allow_empty=False)

    class Meta:
        model = ControlListClassificationQuery
        fields = ['comment', 'report_summary', 'control_code', 'is_good_controlled']

    def __init__(self, *args, **kwargs):
        super(ControlListClassificationQueryResponseSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get('is_good_controlled')):
            self.fields['control_code'] = ControlListEntryField(required=True, write_only=True)

    # pylint: disable = W0221
    def update(self, instance, validated_data):
        instance.comment = validated_data.get('comment')
        instance.report_summary = validated_data.get('report_summary').text
        instance.status = get_case_status_from_status_enum(CaseStatusEnum.FINALISED)

        # Update the good's details
        instance.good.is_good_controlled = validated_data.get('is_good_controlled')
        if instance.good.is_good_controlled:
            instance.good.control_code = validated_data.get('control_code')
        else:
            instance.good.control_code = ''
        instance.good.status = GoodStatus.VERIFIED
        instance.good.save()

        instance.save()
        return instance
