import reversion
from django.db import transaction
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressSerializer
from content_strings.strings import get_string
from organisations.models import Organisation, Site, ExternalLocation
from static.countries.models import Country
from users.serializers import ExporterUserCreateUpdateSerializer


class SiteCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={'blank': 'Enter a name for your site'})
    address = AddressSerializer(write_only=True)
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = Site
        fields = ('id', 'name', 'address', 'organisation')

    @transaction.atomic
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address_data['country'] = address_data['country'].id

        address_serializer = AddressSerializer(data=address_data)
        with reversion.create_revision():
            if address_serializer.is_valid():
                address = Address(**address_serializer.validated_data)
                address.save()
            else:
                raise serializers.ValidationError(address_serializer.errors)

        site = Site.objects.create(address=address, **validated_data)
        return site

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        address_data = validated_data.pop('address')
        address_serializer = AddressSerializer(instance.address, partial=True, data=address_data)
        if address_serializer.is_valid():
            instance.address.address_line_1 = address_serializer.validated_data.get('address_line_1',
                                                                                    instance.address.address_line_1)
            instance.address.address_line_2 = address_serializer.validated_data.get('address_line_2',
                                                                                    instance.address.address_line_2)
            instance.address.region = address_serializer.validated_data.get('region',
                                                                            instance.address.region)
            instance.address.postcode = address_serializer.validated_data.get('postcode',
                                                                              instance.address.postcode)
            instance.address.city = address_serializer.validated_data.get('city',
                                                                          instance.address.city)
            instance.address.country = address_serializer.validated_data.get('country', instance.address.country)
            instance.address.save()
        else:
            return address_serializer.errors

        return instance


class OrganisationCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    user = ExporterUserCreateUpdateSerializer(write_only=True)
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
        site_data['address']['country'] = site_data['address']['country'].id

        site_serializer = SiteCreateSerializer(data=site_data)
        with reversion.create_revision():
            if site_serializer.is_valid():
                site = site_serializer.save()
            else:
                raise serializers.ValidationError(site_serializer.errors)

        user_serializer = ExporterUserCreateUpdateSerializer(data=user_data)
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


class ExternalLocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(),
                                                 error_messages={'null': get_string('address.null_country')})
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = ExternalLocation
        fields = ('id',
                  'name',
                  'address',
                  'country',
                  'organisation')
