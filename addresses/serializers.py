from rest_framework import serializers

from addresses.models import Address


class AddressBaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('id',
                  'country',
                  'address_line_1',
                  'address_line_2',
                  'state',
                  'zip_code',
                  'city')
