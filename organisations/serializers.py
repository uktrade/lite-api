from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressBaseSerializer, AddressViewSerializer
from organisations.models import Organisation, Site
from users.models import User
from users.serializers import UserCreateSerializer


class SiteCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = AddressBaseSerializer(many=False, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'address')


class OrganisationCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    user = UserCreateSerializer(many=False, write_only=True)
    site = SiteCreateSerializer(many=False, write_only=True)

    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number',
                  'created_at',
                  'last_modified_at',
                  'user',
                  'site')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        site_data = validated_data.pop('site')
        address_data = site_data.pop('address')

        address = Address.objects.create(**address_data)
        organisation = Organisation.objects.create(**validated_data)

        Address.objects.create(**address_data)
        User.objects.create(organisation=organisation, **user_data)
        site = Site.objects.create(organisation=organisation, address=address, **site_data)

        organisation.primary_site = site
        organisation.save()

        return organisation


class SiteViewSerializer(serializers.ModelSerializer):
    address = AddressViewSerializer()

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address')


class OrganisationViewSerializer(serializers.ModelSerializer):
    primary_site = SiteViewSerializer()

    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number',
                  'primary_site',
                  'created_at',
                  'last_modified_at')


class OrganisationUpdateSerializer(OrganisationViewSerializer):
    primary_site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    def update(self, instance, validated_data):
        """
        Update and return an existing `Organisation` instance, given the validated data.
        """
        instance.primary_site = validated_data.get('primary_site', instance.primary_site)
        instance.save()
        return instance
