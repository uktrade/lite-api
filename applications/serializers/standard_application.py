from applications.models import StandardApplication
from applications.serializers.serializers import DraftApplicationCreateSerializer


class StandardApplicationCreateSerializer(DraftApplicationCreateSerializer):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data['organisation'] = self.context.id

    class Meta:
        model = StandardApplication
        fields = ['id',
                  'name',
                  'application_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation']
