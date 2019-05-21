from rest_framework import serializers


class EndUserCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all(), required=False)

    class Meta:
        model = User
        fields = ('id', 'name', 'address', 'organisation')

    def create(self, validated_data):
        address_data = validated_data.pop('address')
        address = Address.objects.create(**address_data)
        site = Site.objects.create(address=address, **validated_data)
        return site