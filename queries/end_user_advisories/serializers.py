from datetime import datetime, timezone

from rest_framework import serializers

from cases.enums import CaseTypeEnum
from conf.serializers import PrimaryKeyRelatedSerializerField
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from parties.enums import SubType
from parties.serializers import EndUserSerializer
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status, get_status_value_from_case_status_enum


class EndUserAdvisorySerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )
    end_user = EndUserSerializer()
    reasoning = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    contact_email = serializers.EmailField()
    copy_of = serializers.PrimaryKeyRelatedField(queryset=EndUserAdvisoryQuery.objects.all(), required=False)
    status = serializers.SerializerMethodField()

    class Meta:
        model = EndUserAdvisoryQuery
        fields = (
            "id",
            "end_user",
            "reasoning",
            "note",
            "organisation",
            "copy_of",
            "nature_of_business",
            "contact_name",
            "contact_email",
            "contact_job_title",
            "contact_telephone",
            "status",
        )

    standard_blank_error_message = "This field may not be blank"

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None

    def validate_nature_of_business(self, value):
        if self.initial_data.get("end_user").get("sub_type") == SubType.COMMERCIAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def validate_contact_name(self, value):
        if self.initial_data.get("end_user").get("sub_type") != SubType.INDIVIDUAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def validate_contact_job_title(self, value):
        if self.initial_data.get("end_user").get("sub_type") != SubType.INDIVIDUAL and not value:
            raise serializers.ValidationError(self.standard_blank_error_message)
        return value

    def create(self, validated_data):
        end_user_data = validated_data.pop("end_user")

        # We set the country and organisation back to their string IDs, otherwise
        # the end_user serializer struggles to save them
        end_user_data["country"] = end_user_data["country"].id
        end_user_data["organisation"] = end_user_data["organisation"].id

        end_user_serializer = EndUserSerializer(data=end_user_data)
        if end_user_serializer.is_valid():
            end_user = end_user_serializer.save()
        else:
            raise serializers.ValidationError({"errors": end_user_serializer.errors})
        validated_data["type"] = CaseTypeEnum.END_USER_ADVISORY_QUERY
        validated_data["organisation_id"] = end_user_data["organisation"]
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.SUBMITTED)
        validated_data["submitted_at"] = datetime.now(timezone.utc)
        end_user_advisory_query = EndUserAdvisoryQuery.objects.create(**validated_data, end_user=end_user)
        end_user_advisory_query.save()

        return end_user_advisory_query
