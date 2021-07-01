from django.http import JsonResponse
from rest_framework import status

from api.core.helpers import str_to_bool


def flatten_errors(errors, data):
    pv_grading_errors = errors.pop("pv_grading_details", {})
    firearm_errors = errors.pop("firearm_details", {})
    # The errors need to be flattened otherwise they will be contained within
    # nested 'pv_grading_details', 'firearm_details' and 'document_on_organisation' dictionaries
    document_on_organisation_errors = firearm_errors.pop("document_on_organisation", {})

    flattened_errors = {
        **errors,
        **firearm_errors,
        **pv_grading_errors,
        **document_on_organisation_errors,
    }
    if data.get("firearm_details"):
        if (
            data["firearm_details"].get("rfd_status") is True
            and "is_covered_by_firearm_act_section_one_two_or_five" in flattened_errors
        ):
            flattened_errors["is_covered_by_firearm_act_section_one_two_or_five"] = [
                "Select yes if the product is covered by section 5 of the Firearms Act 1968"
            ]

    return flattened_errors


def create_or_update_good(serializer, data, is_created):
    if not serializer.is_valid():
        flattened_errors = flatten_errors(serializer.errors, data)
        return JsonResponse(data={"errors": flattened_errors}, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    if str_to_bool(data.get("validate_only")):
        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    return JsonResponse(
        data={"good": serializer.data}, status=status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    )
