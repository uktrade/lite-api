from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressSerializer
from organisations.models import Organisation, Site
from users.models import User
from users.serializers import UserCreateSerializer


class SiteCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = AddressSerializer(many=False, write_only=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('id', 'name', 'address', 'organisation')

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        Address.objects.create(**address_data)
        site = Site.objects.create(address=address, **validated_data)
        return site


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

        organisation = Organisation.objects.create(**validated_data)

        user_data['organisation'] = organisation.id

        site_serializer = SiteCreateSerializer(data=site_data)
        site = None
        if site_serializer.is_valid():
            site = site_serializer.save()

        user_serializer = UserCreateSerializer(data=user_data)
        if user_serializer.is_valid():
            user_serializer.save()

        organisation.primary_site = site
        organisation.save()

        return organisation


class SiteViewSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

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


class SiteUpdateSerializer(OrganisationViewSerializer):
    name = serializers.CharField()
    address = AddressSerializer(many=False, write_only=True)

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address')

    def update(self, instance, validated_data):
        """
        Update and return an existing `Site` instance, given the validated data.
        """
        address_data = validated_data.pop('address')
        instance.name = validated_data.get('name', instance.name)

        address_serializer = AddressSerializer(Address.objects.get(pk=instance.address.id),
                                               data=address_data)
        if address_serializer.is_valid():
            address_serializer.save()

        instance.save()
        return instance
