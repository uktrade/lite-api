from rest_framework import serializers

from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from addresses.serializers import AddressSerializer
from compliance.enums import ComplianceRiskValues, ComplianceVisitTypes
from compliance.models import ComplianceVisitCase
from conf.serializers import PrimaryKeyRelatedSerializerField
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer

from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum


# ComplianceVisitCases have a number of textfields, this constant is for serializers to ensure max length on validation
#   database doesn't enforce this max length
COMPLIANCEVISITCASE_TEXTFIELD_LENGTH = 750


class ComplianceVisitViewSerializer(serializers.ModelSerializer):
    site_case = serializers.UUIDField()
    site_name = serializers.CharField(source="site_case.site.name")
    address = AddressSerializer(source="site_case.site.address")
    status = serializers.SerializerMethodField()
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationDetailSerializer
    )
    overall_risk_value = KeyValueChoiceField(choices=ComplianceRiskValues.choices, allow_null=True, allow_blank=True,)
    compliance_risk_value = KeyValueChoiceField(
        choices=ComplianceRiskValues.choices, allow_null=True, allow_blank=True,
    )
    individuals_risk_value = KeyValueChoiceField(
        choices=ComplianceRiskValues.choices, allow_null=True, allow_blank=True,
    )
    products_risk_value = KeyValueChoiceField(choices=ComplianceRiskValues.choices, allow_null=True, allow_blank=True,)
    visit_type = KeyValueChoiceField(choices=ComplianceVisitTypes.choices, allow_null=True, allow_blank=True,)
    licence_risk_value = serializers.IntegerField(min_value=1, max_value=5, allow_null=True,)

    class Meta:
        model = ComplianceVisitCase
        fields = (
            "id",
            "site_case",
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
        )

    def get_status(self, instance):
        if instance.status:
            return {
                "key": instance.status.status,
                "value": get_status_value_from_case_status_enum(instance.status.status),
            }
        return None
