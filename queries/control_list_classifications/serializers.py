from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField
from goods.serializers import GoodWithFlagsSerializer
from organisations.models import Organisation
from organisations.serializers import TinyOrganisationViewSerializer
from queries.control_list_classifications.models import ControlListClassificationQuery


class ControlListClassificationQuerySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(queryset=Organisation.objects.all(),
                                                    serializer=TinyOrganisationViewSerializer)
    good = GoodWithFlagsSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ControlListClassificationQuery
        fields = ['id', 'details', 'good', 'submitted_at', 'organisation']

