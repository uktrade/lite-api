from django.http import JsonResponse
from rest_framework import status

from api.core.helpers import str_to_bool


def create_or_update_good(serializer, data, is_created):
    if not serializer.is_valid():
        errors = serializer.errors
        pv_grading_errors = errors.pop("pv_grading_details", None)
        firearm_errors = errors.pop("firearm_details", None)
        # The errors need to be flattened otherwise they will be contained within a 'pv_grading_details' dict
        if firearm_errors:
            flattened_errors = (
                {**errors, **firearm_errors, **pv_grading_errors} if pv_grading_errors else {**errors, **firearm_errors}
            )
            if (
                data["firearm_details"].get("rfd_status") is True
                and "is_covered_by_firearm_act_section_one_two_or_five" in flattened_errors
            ):
                flattened_errors["is_covered_by_firearm_act_section_one_two_or_five"] = [
                    "Select yes if the product is covered by section 5 of the Firearms Act 1968"
                ]

        else:
            flattened_errors = {**errors, **pv_grading_errors} if pv_grading_errors else errors
        return JsonResponse(data={"errors": flattened_errors}, status=status.HTTP_400_BAD_REQUEST)

    if str_to_bool(data.get("validate_only")):
        return JsonResponse(data={}, status=status.HTTP_200_OK)

    serializer.save()

    return JsonResponse(
        data={"good": serializer.data}, status=status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    )
