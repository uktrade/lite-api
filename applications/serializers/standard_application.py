from rest_framework import serializers

from applications.models import StandardApplication
from applications.serializers.generic_application import GenericApplicationCreateSerializer, \
    GenericApplicationUpdateSerializer


class StandardApplicationViewSerializer(serializers.ModelSerializer):
    # end_user = EndUserSerializer()
    # ultimate_end_users = UltimateEndUserSerializer(many=True)
    # third_parties = ThirdPartySerializer(many=True)
    # consignee = ConsigneeSerializer()
    # goods = GoodOnApplicationWithFlagsViewSerializer(many=True, read_only=True)
    # destinations = serializers.SerializerMethodField()

    class Meta:
        model = StandardApplication
        # fields = [
        #     'end_user',
        #     'ultimate_end_users',
        #     'third_parties',
        #     'consignee',
        #     'goods',
        #     'destinations',
        # ]
        fields = '__all__'

    # def get_destinations(self, application):
    #     if application.end_user:
    #         serializer = EndUserSerializer(application.end_user)
    #         return {'type': 'end_user', 'data': serializer.data}
    #     else:
    #         return {'type': 'end_user', 'data': ''}


class StandardApplicationCreateSerializer(GenericApplicationCreateSerializer):
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


class StandardApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    class Meta:
        model = StandardApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields
