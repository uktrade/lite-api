from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.models import Address
from addresses.serializers import AddressBaseSerializer
from organisations.models import Organisation, Site
from users.models import User


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


class SiteSerializer(serializers.ModelSerializer):
    address = PrimaryKeyRelatedField(queryset=Address.objects.all())
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address',
                  'organisation')


class SiteViewSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    address = AddressBaseSerializer(read_only=True)

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address',
                  'organisation')


class SiteUpdateSerializer(OrganisationViewSerializer):
    name = serializers.CharField()
    address = PrimaryKeyRelatedField(queryset=Address.objects.all())
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    def update(self, instance, validated_data):
        """
        Update and return an existing `Site` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.organisation = validated_data.get('organisation', instance.organisation)
        instance.save()
        return instance


class OrganisationInitialSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    primary_site = SiteSerializer(read_only=True)
    admin_user_first_name = serializers.CharField()
    admin_user_last_name = serializers.CharField()
    admin_user_email = serializers.EmailField(
        error_messages={'invalid': 'Enter an email address in the correct format, like name@example.com'})

    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number',
                  'primary_site',
                  'admin_user_first_name',
                  'admin_user_last_name',
                  'admin_user_email',
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


class OrganisationValidateFormSection(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()

    class Meta:
        model = Organisation
        fields = ('name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number')


class SiteValidateFormSection(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'name',
                  'country',
                  'address_line_1',
                  'address_line_2',
                  'state',
                  'zip_code',
                  'city')


class UserValidateFormSection(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'first_name',
                  'last_name',
                  'email',
                  'password')
