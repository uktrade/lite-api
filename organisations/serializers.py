from rest_framework import serializers
from organisations.models import Organisation


class OrganisationInitialSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number = serializers.CharField()
    vat_number = serializers.CharField()
    address = serializers.CharField()
    admin_user_email = serializers.CharField()

    class Meta:
        model = Organisation
        fields = ('id',
                  'name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
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
                  'address',
                  'created_at',
                  'last_modified_at')
