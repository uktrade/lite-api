from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField
from goods.serializers import FullGoodSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from queries.control_list_classifications.models import ControlListClassificationQuery
from static.statuses.models import CaseStatus


class ClcQuerySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(queryset=Organisation.objects.all(),
                                                    serializer=TinyOrganisationViewSerializer)
    good = FullGoodSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ControlListClassificationQuery
        fields = (
            'id',
            'details',
            'good',
            'submitted_at',
            'organisation')


class ClcQueryUpdateSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

    class Meta:
        model = ControlListClassificationQuery
        fields = (
            'id',
            'status',
            'organisation')

    # pylint: disable = W0221
    def update(self, instance, partial):
        instance.status = partial.get('status', instance.status)
        instance.save()
        return instance
