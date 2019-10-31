from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.enums import ApplicationType
from applications.models import HmrcQuery
from conf.serializers import KeyValueChoiceField
from organisations.enums import OrganisationType
from organisations.models import Organisation


class HmrcQueryViewSerializer(serializers.ModelSerializer):
    application_type = KeyValueChoiceField(choices=ApplicationType.choices)

    class Meta:
        model = HmrcQuery
        fields = [
            'id',
            'reasoning',
            'application_type'
        ]


class HmrcQueryCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    hmrc_organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.context.type != OrganisationType.HMRC:
            raise exceptions.PermissionDenied('User does not belong to an HMRC organisation')

        self.initial_data['hmrc_organisation'] = self.context.id

    class Meta:
        model = HmrcQuery
        fields = [
            'reasoning',
            'application_type',
            'organisation',
            'hmrc_organisation'
        ]


class HmrcQueryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HmrcQuery
        fields = ['reasoning']
