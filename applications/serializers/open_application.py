from applications.models import OpenApplication
from applications.serializers.serializers import DraftApplicationCreateSerializer


class OpenApplicationCreateSerializer(DraftApplicationCreateSerializer):

    def __init__(self, *args, **kwargs):
        super(OpenApplicationCreateSerializer, self).__init__(*args, **kwargs)
        self.initial_data['organisation'] = self.context.id

    class Meta:
        model = OpenApplication
        fields = ['id',
                  'name',
                  'application_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation']
