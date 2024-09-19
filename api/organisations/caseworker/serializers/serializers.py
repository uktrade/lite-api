from typing import Dict

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from api.organisations.models import Organisation, Site
from api.users.enums import UserType
from api.users.models import (
    ExporterUser,
    BaseUser,
    UserOrganisationRelationship,
    Role,
)


class ExporterUserCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    email = serializers.EmailField(required=True)
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=Organisation.objects.all(), required=True, write_only=True
    )
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), write_only=True, required=True)
    sites = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all(), write_only=True, many=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)

    class Meta:
        model = ExporterUser
        fields = (
            "id",
            "email",
            "phone_number",
            "role",
            "organisation",
            "sites",
        )

    def validate_email(self, email):
        return email.lower()

    def create(self, validated_data: Dict):
        phone_number = validated_data.pop("phone_number", "")
        email = validated_data.pop("email")
        organisation = validated_data.pop("organisation")
        sites = validated_data.pop("sites")
        role = validated_data.pop("role")
        base_user_defaults = {
            "email": email,
            "phone_number": phone_number,
        }

        if phone_number:
            phone_number = phone_number.as_e164

        base_user, _ = BaseUser.objects.get_or_create(
            email__iexact=email, type=UserType.EXPORTER, defaults=base_user_defaults
        )
        exporter, _ = ExporterUser.objects.get_or_create(baseuser_ptr=base_user, defaults=validated_data)
        relationship = UserOrganisationRelationship(user=exporter, organisation=organisation, role=role)
        relationship.save()
        relationship.sites.set(sites)

        return exporter
