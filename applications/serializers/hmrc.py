from rest_framework import exceptions
from rest_framework import serializers

from applications.models import HmrcQuery
from organisations.enums import OrganisationType


class HmrcQueryViewSerializer(serializers.ModelSerializer):
    # application_type = KeyValueChoiceField(choices=ApplicationType.choices)

    class Meta:
        model = HmrcQuery
        fields = ['id', 'reasoning', 'application_type']


class HmrcQueryCreateSerializer(serializers.ModelSerializer):
    # application_type = KeyValueChoiceField(choices=ApplicationType.choices)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.context.type is not OrganisationType.HMRC:
            raise exceptions.PermissionDenied('User does not belong to an HMRC organisation')

        self.initial_data['hmrc_organisation'] = self.context.id

    class Meta:
        model = HmrcQuery
        fields = ['id', 'reasoning', 'application_type']


class HmrcQueryUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = HmrcQuery
        fields = ['reasoning']
