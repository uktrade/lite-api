from audit_trail import service as audit_trail_service
from django.http import JsonResponse
from rest_framework import status

from audit_trail.payload import AuditType

END_USE_FIELDS = [
    "is_military_end_use_controls",
    "military_end_use_controls_ref",
    "is_informed_wmd",
    "informed_wmd_ref",
    "is_suspected_wmd",
    "suspected_wmd_ref",
    "is_eu_military",
]


def edit_end_use_details(application, request):
    if not application.is_major_editable():
        for field in END_USE_FIELDS:
            response_error = end_use_helper(request, field)
            if response_error:
                return response_error


def end_use_helper(request, field):
    if request.data.get(field):
        return JsonResponse(
            data={"errors": {field: ["This isn't possible on a minor edit"]}}, status=status.HTTP_400_BAD_REQUEST,
        )


def get_old_end_use_details_fields(application):
    return {end_use_field: getattr(application, end_use_field) for end_use_field in END_USE_FIELDS}


def get_new_end_use_details_fields(validated_data):
    new_end_use_details = {}
    for end_use_field in END_USE_FIELDS:
        if end_use_field in validated_data:
            new_end_use_details[end_use_field] = validated_data[end_use_field]
    return new_end_use_details


def audit_end_use_details(user, case, old_end_use_details_fields, new_end_use_details_fields):
    for key, new_end_use_value in new_end_use_details_fields.items():
        old_end_use_value = old_end_use_details_fields[key]
        if new_end_use_value != old_end_use_value:
            audit_trail_service.create(
                actor=user,
                verb=AuditType.UPDATE_APPLICATION_END_USE_DETAILS,
                target=case,
                payload={
                    "end_use_detail": key,
                    "old_end_use_detail": old_end_use_value,
                    "new_end_use_detail": new_end_use_value,
                },
            )


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
    old_have_you_been_informed = application.have_you_been_informed == "yes"
    have_you_been_informed = request.data.get("have_you_been_informed")

    if have_you_been_informed:
        old_ref_number = application.reference_number_on_information_form or "no reference"

        serializer.save()

        new_ref_number = application.reference_number_on_information_form or "no reference"

        if old_have_you_been_informed and not have_you_been_informed == "yes":
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
