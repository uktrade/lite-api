from rest_framework import serializers


from api.audit_trail.models import Audit
from api.applications.models import StandardApplication
from api.cases.models import EcjuQuery
from api.staticdata.statuses.enums import CaseStatusEnum


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


def get_last_application(obj):
    if not obj.superseded_by:
        return obj
    return get_last_application(obj.superseded_by)


class ApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = ("id",)

    def get_id(self, application):
        application = get_original_application(application)
        return application.pk


class RFISerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField(required=False)
    closed_at = serializers.SerializerMethodField(required=False)

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "application_id",
            "created_at",
            "closed_at",
        )

    def get_application_id(self, rfi):
        return get_original_application(rfi.case).pk

    def get_closed_at(self, rfi):
        return rfi.responded_at


class StatusChangeSerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField(required=False)
    changed_at = serializers.SerializerMethodField(required=False)
    status = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Audit
        fields = (
            "id",
            "application_id",
            "changed_at",
            "status",
        )

    def get_application_id(self, audit):
        application = get_original_application(audit.target)
        return application.pk

    def get_changed_at(self, audit):
        return audit.created_at

    def get_status(self, audit):
        status = audit.payload["status"]["new"].lower().replace(" ", "_").replace("-", "")
        if status not in CaseStatusEnum.all():
            raise ValueError(f"Unknown status {status}")
        return status


class StatusSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField(required=False)
    is_terminal = serializers.SerializerMethodField(required=False)
    is_closed = serializers.SerializerMethodField(required=False)

    def get_name(self, status_name):
        return status_name

    def get_is_terminal(self, status_name):
        return CaseStatusEnum.is_terminal(status_name)

    def get_is_closed(self, status_name):
        return CaseStatusEnum.is_closed(status_name)


class NonWorkingDaySerializer(serializers.Serializer):
    date = serializers.SerializerMethodField(required=False)

    def get_date(self, date):
        return date


class StandardApplicationSerializer(serializers.ModelSerializer):
    destination = serializers.SerializerMethodField(required=False)
    # is_amended = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "created_at",
            "updated_at",
            "export_type",
            "reference_code",
            "name",
            "activity",
            "is_eu_military",
            "is_informed_wmd",
            "is_suspected_wmd",
            "is_compliant_limitations_eu",
            "is_military_end_use_controls",
            "intended_end_use",
            "agreed_to_foi",
            "foi_reason",
            "reference_number_on_information_form",
            "have_you_been_informed",
            "is_shipped_waybill_or_lading",
            "is_temp_direct_control",
            "proposed_return_date",
            "sla_days",
            "sla_remaining_days",
            "sla_updated_at",
            "submitted_at",
            "submitted_by",
            "copy_of_id",
            # "is_amended",
            "case_officer_id",
            "status_id",
            "case_type_id",
            "organisation_id",
            "destination",
            "goods_starting_point",
            "amendment_of_id",
        )

    def get_destination(self, standard_application):
        if getattr(standard_application, "end_user", None):
            party = standard_application.end_user.party
            return party.country.id

        return ""

    # def get_is_amended(self, instance):
    #     """Determines whether an application is major/minor edited using Audit logs
    #     and returns True if either of the amends are done, False otherwise"""
    #     audit_qs = Audit.objects.filter(target_object_id=instance.id)
    #     is_reference_name_updated = audit_qs.filter(verb=AuditType.UPDATED_APPLICATION_NAME).exists()
    #     is_product_removed = audit_qs.filter(verb=AuditType.REMOVE_GOOD_FROM_APPLICATION).exists()
    #     app_letter_ref_updated = audit_qs.filter(
    #         Q(
    #             verb__in=[
    #                 AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
    #                 AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
    #                 AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
    #             ]
    #         )
    #     )
    #     # in case of doing major edits then the status is set as "Applicant editing"
    #     # Here we are detecting the transition from "Submitted" -> "Applicant editing"
    #     for item in audit_qs.filter(verb=AuditType.UPDATED_STATUS):
    #         status = item.payload["status"]
    #         if status["old"] == CaseStatusEnum.get_text(CaseStatusEnum.SUBMITTED) and status[
    #             "new"
    #         ] == CaseStatusEnum.get_text(CaseStatusEnum.APPLICANT_EDITING):
    #             return True

    #     return any([is_reference_name_updated, app_letter_ref_updated, is_product_removed])
