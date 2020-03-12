from audit_trail import service as audit_trail_service
from django.http import JsonResponse
from rest_framework import status

from audit_trail.payload import AuditType
from conf.helpers import str_to_bool
from lite_content.lite_api.strings import Applications as strings

END_USE_FIELDS = {
    "is_military_end_use_controls": strings.Generic.EndUseDetails.Audit.INFORMED_TO_APPLY_TITLE,
    "military_end_use_controls_ref": strings.Generic.EndUseDetails.Audit.INFORMED_TO_APPLY_REF,
    "is_informed_wmd": strings.Generic.EndUseDetails.Audit.INFORMED_WMD_TITLE,
    "informed_wmd_ref": strings.Generic.EndUseDetails.Audit.INFORMED_WMD_REF,
    "is_suspected_wmd": strings.Generic.EndUseDetails.Audit.SUSPECTED_WMD_TITLE,
    "suspected_wmd_ref": strings.Generic.EndUseDetails.Audit.SUSPECTED_WMD_REF,
    "is_eu_military": strings.Generic.EndUseDetails.Audit.EU_MILITARY_TITLE,
    "is_compliant_limitations_eu": strings.Generic.EndUseDetails.Audit.COMPLIANT_LIMITATIONS_EU_TITLE,
    "compliant_limitations_eu_ref": strings.Generic.EndUseDetails.Audit.COMPLIANT_LIMITATIONS_EU_REF,
}


def edit_end_use_details(application, request):
    if not application.is_major_editable():
        for field in END_USE_FIELDS.keys():
            response_error = end_use_helper(request, field)
            if response_error:
                return response_error


def end_use_helper(request, field):
    if field in request.data:
        return JsonResponse(
            data={"errors": {field: [strings.Generic.NOT_POSSIBLE_ON_MINOR_EDIT]}}, status=status.HTTP_400_BAD_REQUEST,
        )


def get_old_end_use_details_fields(application):
    return {end_use_field: getattr(application, end_use_field) for end_use_field in END_USE_FIELDS.keys()}


def get_new_end_use_details_fields(validated_data):
    new_end_use_details = {}
    for end_use_field in END_USE_FIELDS.keys():
        if end_use_field in validated_data:
            new_end_use_details[end_use_field] = validated_data[end_use_field]
    return new_end_use_details


def audit_end_use_details(user, case, old_end_use_details_fields, new_end_use_details_fields):
    for key, new_end_use_value in new_end_use_details_fields.items():
        old_end_use_value = old_end_use_details_fields[key]
        if new_end_use_value != old_end_use_value:
            old_end_use_value, new_end_use_value = _transform_values(old_end_use_value, new_end_use_value)
            audit_trail_service.create(
                actor=user,
                verb=AuditType.UPDATE_APPLICATION_END_USE_DETAIL,
                target=case,
                payload={
                    "end_use_detail": END_USE_FIELDS[key],
                    "old_end_use_detail": old_end_use_value,
                    "new_end_use_detail": new_end_use_value,
                },
            )


def _transform_values(old_end_use_value, new_end_use_value):
    if isinstance(old_end_use_value, bool):
        old_end_use_value = "Yes" if old_end_use_value else "No"

    if isinstance(new_end_use_value, bool):
        new_end_use_value = "Yes" if new_end_use_value else "No"

    return old_end_use_value, new_end_use_value


def save_and_audit_end_use_details(request, application, serializer):
    old_end_use_details_fields = get_old_end_use_details_fields(application)
    new_end_use_details_fields = get_new_end_use_details_fields(serializer.validated_data)
    if new_end_use_details_fields:
        serializer.save()
        audit_end_use_details(
            request.user, application.get_case(), old_end_use_details_fields, new_end_use_details_fields
        )
        return True


def save_and_audit_have_you_been_informed_ref(request, application, serializer):
    old_have_you_been_informed = application.have_you_been_informed
    have_you_been_informed = request.data.get("have_you_been_informed")

    if have_you_been_informed:
        old_ref_number = application.reference_number_on_information_form or "no reference"

        serializer.save()

        new_ref_number = application.reference_number_on_information_form or "no reference"

        if old_have_you_been_informed and not str_to_bool(have_you_been_informed):
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                target=application.get_case(),
                payload={"old_ref_number": old_ref_number},
            )
        else:
            if old_have_you_been_informed:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                    target=application.get_case(),
                    payload={"old_ref_number": old_ref_number, "new_ref_number": new_ref_number},
                )
            else:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                    target=application.get_case(),
                    payload={"new_ref_number": new_ref_number},
                )
        return True
