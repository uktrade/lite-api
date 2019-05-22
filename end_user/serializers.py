from rest_framework import serializers

from end_user.models import EndUser
from organisations.models import Organisation
from organisations.serializers import OrganisationViewSerializer


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
                  'country',
                  'website',
                  'type'
                  'organisation')

    def create(self, validated_data):
        end_user = EndUser.objects.create(**validated_data)
        return end_user


class EndUserViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'website',
                  'type',
                  'organisation')


class EndUserUpdateSerializer(OrganisationViewSerializer):
    name = serializers.CharField()

    class Meta:
        model = EndUser
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'website',
                  'type',
                  'organisation')

    def update(self, instance, validated_data):
        """
        Update and return an existing `Site` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.country = validated_data.get('country', instance.country)
        instance.website = validated_data.get('website', instance.website)
        instance.type = validated_data.get('type', instance.type)
        instance.save()
        return instance

''' 
class AddressUpdateSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'postcode',
                  'city',
                  'region',
                  'country')

    def update(self, instance, validated_data):
        instance.address_line_1 = validated_data.get('address_line_1', instance.address_line_1)
        instance.address_line_2 = validated_data.get('address_line_2', instance.address_line_2)
        instance.postcode = validated_data.get('postcode', instance.postcode)
        instance.city = validated_data.get('city', instance.city)
        instance.region = validated_data.get('region', instance.region)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance
'''
