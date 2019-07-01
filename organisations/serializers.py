import reversion
from django.db import transaction
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressCountrylessSerializer, AddressSerializer
from organisations.models import Organisation, Site, ExternalLocation
from static.countries.helpers import get_country
from static.countries.models import Country
from users.serializers import UserCreateSerializer


class SiteCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    # TODO: Simplify country process
    address = AddressCountrylessSerializer(write_only=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = Site
        fields = ('id', 'name', 'address', 'organisation')

    @transaction.atomic
    def create(self, validated_data):
        address_data = validated_data.pop('address')

        address_serializer = AddressCountrylessSerializer(data=address_data)
        with reversion.create_revision():
            if address_serializer.is_valid():
                # TODO: Simplify country process
                data = address_serializer.data
                country = get_country(data['country'])
                del data['country']
                address = Address(**data, country=country)
                address.save()
            else:
                raise serializers.ValidationError(address_serializer.errors)

        site = Site.objects.create(address=address, **validated_data)
        return site


class OrganisationCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    user = UserCreateSerializer(write_only=True)
    site = SiteCreateSerializer(write_only=True)

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

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        site_data = validated_data.pop('site')

        organisation = Organisation.objects.create(**validated_data)
        user_data['organisation'] = organisation.id

        site_serializer = SiteCreateSerializer(data=site_data)
        with reversion.create_revision():
            if site_serializer.is_valid():
                site = site_serializer.save()
            else:
                raise serializers.ValidationError(site_serializer.errors)

        user_serializer = UserCreateSerializer(data=user_data)
        with reversion.create_revision():
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                raise serializers.ValidationError(user_serializer.errors)

        organisation.primary_site = site
        organisation.save()

        organisation.primary_site.organisation = organisation
        organisation.primary_site.save()

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
        address_serializer = AddressSerializer(Address.objects.get(pk=instance.address.id),
                                               data=address_data,
                                               partial=True)
        if address_serializer.is_valid():
            address_serializer.save()

        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class ExternalLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = ExternalLocation
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'organisation')
