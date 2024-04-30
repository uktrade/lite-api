from django.db.models import Q
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import OpenApplication
from api.applications.mixins.serializers import PartiesSerializerMixin

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.licences.models import Licence
from api.licences.serializers.view_licence import CaseLicenceViewSerializer
from api.organisations.models import Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from api.staticdata.statuses.serializers import CaseSubStatusSerializer


from .good import GoodOnApplicationViewSerializer
from .generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
)


class OpenApplicationCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = OpenApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + ("goods_category",)

    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id
        self.initial_data["organisation"] = self.context.id

    def create(self, validated_data):
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return super().create(validated_data)


class OpenApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenApplication
        fields = (
            "name",
            "nature_of_products",
            "siels_issued_last_year",
            "number_of_siels_last_year",
            "destination_countries",
            "purely_commercial",
        )


class OpenApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):

    class Meta:
        model = OpenApplication
        fields = GenericApplicationViewSerializer.Meta.fields


class OpenApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    destinations = serializers.SerializerMethodField()
    additional_documents = serializers.SerializerMethodField()
    licence = serializers.SerializerMethodField()
    sanction_matches = serializers.SerializerMethodField()
    is_amended = serializers.SerializerMethodField()
    sub_status = CaseSubStatusSerializer()

    class Meta:
        model = OpenApplication
        fields = (
            GenericApplicationViewSerializer.Meta.fields
            + PartiesSerializerMixin.Meta.fields
            + (
                "goods",
                "activity",
                "usage",
                "destinations",
                "additional_documents",
                "is_military_end_use_controls",
                "military_end_use_controls_ref",
                "is_informed_wmd",
                "informed_wmd_ref",
                "is_suspected_wmd",
                "suspected_wmd_ref",
                "is_eu_military",
                "is_compliant_limitations_eu",
                "compliant_limitations_eu_ref",
                "intended_end_use",
                "licence",
                "sanction_matches",
                "is_amended",
                "appeal_deadline",
                "appeal",
                "sub_status",
                "nature_of_products",
                "siels_issued_last_year",
                "number_of_siels_last_year",
                "destination_countries",
                "purely_commercial",
            )
        )

    def get_licence(self, instance):
        licence = Licence.objects.filter(case=instance).first()
        if licence:
            return CaseLicenceViewSerializer(licence).data

    def get_is_amended(self, instance):
        """Determines whether an application is major/minor edited using Audit logs
        and returns True if either of the amends are done, False otherwise"""
        audit_qs = Audit.objects.filter(target_object_id=instance.id)
        is_reference_name_updated = audit_qs.filter(verb=AuditType.UPDATED_APPLICATION_NAME).exists()
        is_product_removed = audit_qs.filter(verb=AuditType.REMOVE_GOOD_FROM_APPLICATION).exists()
        app_letter_ref_updated = audit_qs.filter(
            Q(
                verb__in=[
                    AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                    AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                    AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                ]
            )
        )
        # in case of doing major edits then the status is set as "Applicant editing"
        # Here we are detecting the transition from "Submitted" -> "Applicant editing"
        for item in audit_qs.filter(verb=AuditType.UPDATED_STATUS):
            status = item.payload["status"]
            if status["old"] == CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED) and status[
                "new"
            ] == CaseStatusEnum.get_text(CaseStatusEnum.APPLICANT_EDITING):
                return True

        return any([is_reference_name_updated, app_letter_ref_updated, is_product_removed])
