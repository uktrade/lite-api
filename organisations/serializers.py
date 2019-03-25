from rest_framework import serializers
from organisations.models import Organisation, NewOrganisationRequest


class OrganisationSerializer(serializers.ModelSerializer):
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


class NewOrganisationRequestSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    eori_number = serializers.CharField()
    sic_number= serializers.CharField()
    vat_number = serializers.CharField()
    address = serializers.CharField()
    admin_user_email = serializers.EmailField()

    class Meta:
        model = NewOrganisationRequest
        fields = ('name',
                  'eori_number',
                  'sic_number',
                  'vat_number',
                  'address',
                  'admin_user_email')
