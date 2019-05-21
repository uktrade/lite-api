from rest_framework import serializers

from end_user.models import EndUser
from organisations.models import Organisation


class EndUserCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.CharField()
    website = serializers.CharField()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'website',
                  'type'
                  'organisation')

    def create(self, validated_data):
        site = EndUser.objects.create(**validated_data)
        return site


class EndUserViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'website',
                  'type'
                  'organisation')
