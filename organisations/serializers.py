from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressBaseSerializer
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


class OrganisationViewSerializer(serializers.ModelSerializer):
    primary_site = PrimaryKeyRelatedField(queryset=Site.objects.all())

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


class SiteViewSerializer(serializers.ModelSerializer):
    address = PrimaryKeyRelatedField(queryset=Address.objects.all())
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address',
                  'organisation')


class OrganisationUpdateSerializer(OrganisationViewSerializer):
    primary_site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    def update(self, instance, validated_data):
        """
        Update and return an existing `Organisation` instance, given the validated data.
        """
        instance.primary_site = validated_data.get('primary_site', instance.primary_site)
        instance.save()
        return instance
