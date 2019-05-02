from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from addresses.serializers import AddressBaseSerializer
from organisations.models import Organisation, Site


""""
    # Example

    class TrackSerializer(serializers.ModelSerializer):
        class Meta:
            model = Track
            fields = ('order', 'title', 'duration')

    class AlbumSerializer(serializers.ModelSerializer):
        tracks = TrackSerializer(many=True, read_only=True)

        class Meta:
            model = Album
            fields = ('album_name', 'artist', 'tracks')

"""


class SiteSerializer(serializers.ModelSerializer):
    address = AddressBaseSerializer(read_only=True)

    class Meta:
        model = Site
        fields = ('id',
                  'name',
                  'address')


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
                  'admin_user_email',
                  'created_at',
                  'last_modified_at')


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

