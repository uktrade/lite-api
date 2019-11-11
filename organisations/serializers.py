import reversion
from django.db import transaction
from rest_framework import serializers

from addresses.models import Address
from addresses.serializers import AddressSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from content_strings.strings import get_string
from organisations.models import Organisation, Site, ExternalLocation
from organisations.enums import OrganisationType
from static.countries.models import Country
from users.models import GovUser
from users.serializers import ExporterUserCreateUpdateSerializer


class SiteSerializer(serializers.ModelSerializer):
    name = serializers.CharField(error_messages={'blank': 'Enter a name for your site'}, write_only=True)
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
        instance.name = validated_data['name']
        instance.save()

        address_data = validated_data.pop('address')
        address_data['country'] = address_data['country'].id
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
            raise serializers.ValidationError(address_serializer.errors)

        return instance


class OrganisationCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    type = KeyValueChoiceField(choices=OrganisationType.choices)
    eori_number = serializers.CharField(required=False, allow_blank=True)
    vat_number = serializers.CharField(required=False, allow_blank=True)
    sic_number = serializers.CharField(required=False)
    registration_number = serializers.CharField(required=False)
    user = ExporterUserCreateUpdateSerializer(write_only=True)
    site = SiteSerializer(write_only=True)

    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'type',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number',
                  'created_at',
                  'last_modified_at',
                  'user',
                  'site')

    standard_blank_error_message = 'This field may not be blank'

    def validate_eori_number(self, value):
        if self.initial_data.get('type') != OrganisationType.HMRC and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def validate_sic_number(self, value):
        if self.initial_data.get('type') == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def validate_vat_number(self, value):
        if self.initial_data.get('type') == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def validate_registration_number(self, value):
        if self.initial_data.get('type') == OrganisationType.COMMERCIAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        site_data = validated_data.pop('site')
        organisation = Organisation.objects.create(**validated_data)
        user_data['organisation'] = organisation.id
        site_data['address']['country'] = site_data['address']['country'].id

        site_serializer = SiteSerializer(data=site_data)
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


class TinyOrganisationViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('id',
                  'name')


class OrganisationDetailSerializer(serializers.ModelSerializer):
    primary_site = PrimaryKeyRelatedSerializerField(queryset=Site.objects.all(), serializer=SiteViewSerializer)
    type = KeyValueChoiceField(OrganisationType.choices)
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        # TODO remove try block when other end points adopt generics
        try:
            if isinstance(self.context.get('request').user, GovUser):
                return list(instance.flags.values('id', 'name'))
        except AttributeError:
            return list(instance.flags.values('id', 'name'))

    class Meta:
        model = Organisation
        fields = '__all__'

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
