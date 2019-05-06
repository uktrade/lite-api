from rest_framework import serializers
from organisations.models import Organisation


class OrganisationInitialSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    registration_number = serializers.CharField()
    address = serializers.CharField()
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
                  'admin_user_first_name',
                  'admin_user_last_name',
                  'admin_user_email',
                  'address',
                  'created_at',
                  'last_modified_at')


class OrganisationViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'registration_number',
                  'address',
                  'created_at',
                  'last_modified_at')
