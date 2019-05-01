from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

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
    class Meta:





class OrganisationInitialSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    site_name = serializers.CharField()
    country = serializers.CharField()
    address_line_1 = serializers.CharField()
    address_line_2 = serializers.CharField()
    state = serializers.CharField()
    zip_code = serializers.CharField()
    city = serializers.CharField()
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
                  'site_name',
                  'country',
                  'address_line_1',
                  'address_line_2',
                  'state',
                  'zip_code',
                  'city',
                  'admin_user_first_name',
                  'admin_user_last_name',
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

