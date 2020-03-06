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
    return {end_use_field: validated_data.get(end_use_field) for end_use_field in END_USE_FIELDS}


def audit_end_use_details(user, case, old_end_use_details_fields, validated_data):
    new_end_use_details_fields = get_new_end_use_details_fields(validated_data)

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
