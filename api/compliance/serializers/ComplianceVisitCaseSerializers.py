from rest_framework import serializers
from rest_framework.fields import empty

from lite_content.lite_api import strings

from api.core.serializers import KeyValueChoiceField
from api.addresses.serializers import AddressSerializer
from api.compliance.enums import ComplianceRiskValues, ComplianceVisitTypes
from api.compliance.models import ComplianceVisitCase, CompliancePerson
from api.core.serializers import PrimaryKeyRelatedSerializerField
from api.organisations.models import Organisation
from api.organisations.serializers import OrganisationDetailSerializer

from api.static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


# ComplianceVisitCases have a number of textfields, this constant is for serializers to ensure max length on validation
#   database doesn't enforce this max length
COMPLIANCEVISITCASE_TEXTFIELD_LENGTH = 750


class ComplianceVisitSerializer(serializers.ModelSerializer):
    site_case_reference_code = serializers.CharField(source="site_case.reference_code")
    site_name = serializers.CharField(source="site_case.site.name")
    address = AddressSerializer(source="site_case.site.address")
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )
    overall_risk_value = KeyValueChoiceField(choices=ComplianceRiskValues.choices, allow_blank=True)
    compliance_risk_value = KeyValueChoiceField(
        choices=ComplianceRiskValues.choices,
        error_messages={"invalid_choice": strings.Compliance.VisitCaseSerializer.RISK_VALUE_INVALID_CHOICE},
    )
    individuals_risk_value = KeyValueChoiceField(
        choices=ComplianceRiskValues.choices,
        error_messages={"invalid_choice": strings.Compliance.VisitCaseSerializer.RISK_VALUE_INVALID_CHOICE},
    )
    products_risk_value = KeyValueChoiceField(
        choices=ComplianceRiskValues.choices,
        error_messages={"invalid_choice": strings.Compliance.VisitCaseSerializer.RISK_VALUE_INVALID_CHOICE},
    )
    visit_type = KeyValueChoiceField(choices=ComplianceVisitTypes.choices, allow_blank=True)
    licence_risk_value = serializers.IntegerField(min_value=1, max_value=5, allow_null=True)
    overview = serializers.CharField(max_length=COMPLIANCEVISITCASE_TEXTFIELD_LENGTH)
    inspection = serializers.CharField(max_length=COMPLIANCEVISITCASE_TEXTFIELD_LENGTH)
    compliance_overview = serializers.CharField(
        max_length=COMPLIANCEVISITCASE_TEXTFIELD_LENGTH,
        error_messages={"blank": strings.Compliance.VisitCaseSerializer.OVERVIEW_BLANK},
    )
    individuals_overview = serializers.CharField(
        max_length=COMPLIANCEVISITCASE_TEXTFIELD_LENGTH,
        error_messages={"blank": strings.Compliance.VisitCaseSerializer.OVERVIEW_BLANK},
    )
    products_overview = serializers.CharField(
        max_length=COMPLIANCEVISITCASE_TEXTFIELD_LENGTH,
        error_messages={"blank": strings.Compliance.VisitCaseSerializer.OVERVIEW_BLANK},
    )
    people_present = serializers.SerializerMethodField(read_only=True)
    visit_date = serializers.DateField(allow_null=True)

    class Meta:
        model = ComplianceVisitCase
        fields = (
            "id",
            "site_case_id",
            "site_case_reference_code",
            "site_name",
            "address",
            "status",
            "organisation",
            "site_case",
            "visit_type",
            "visit_date",
            "overall_risk_value",
            "licence_risk_value",
            "overview",
            "inspection",
            "compliance_overview",
            "compliance_risk_value",
            "individuals_overview",
            "individuals_risk_value",
            "products_overview",
            "products_risk_value",
            "people_present",
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None

    def get_people_present(self, instance):
        people = CompliancePerson.objects.filter(visit_case_id=instance.id)
        return [{"id": person.id, "name": person.name, "job_title": person.job_title} for person in people]

    def __init__(self, instance=None, data=empty, **kwargs):
        # If an IntegerField receives a blank field, it throws an error. We don't enforce the user to add the
        #   licence_risk_value field till they desire to regardless of form.
        if data is not empty:
            if data.get("licence_risk_value") == "":
                data.pop("licence_risk_value")
        super(ComplianceVisitSerializer, self).__init__(instance, data, **kwargs)


class CompliancePersonSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Name may not be blank"},
        max_length=100,
    )
    job_title = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Job title may not be blank"},
        max_length=100,
    )

    class Meta:
        model = CompliancePerson
        fields = (
            "id",
            "name",
            "job_title",
        )
