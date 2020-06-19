from rest_framework.exceptions import ValidationError

from goods.enums import Component
from lite_content.lite_api import strings


def validate_component_details(data):
    """ Validate the accompanying details for the chosen 'yes' component option. """
    component = data["is_component"]
    component_detail_options = {
        Component.YES_DESIGNED: {
            "details_field": "designed_details",
            "error": strings.Goods.NO_DESIGN_COMPONENT_DETAILS,
        },
        Component.YES_MODIFIED: {
            "details_field": "modified_details",
            "error": strings.Goods.NO_MODIFIED_COMPONENT_DETAILS,
        },
        Component.YES_GENERAL_PURPOSE: {
            "details_field": "general_details",
            "error": strings.Goods.NO_GENERAL_COMPONENT_DETAILS,
        },
    }

    field = component_detail_options[component]["details_field"]
    error = component_detail_options[component]["error"]

    if not data[field]:
        return {"is_valid": False, "details_field": field, "error": error}
    else:
        return {"is_valid": True, "details_field": field}


def validate_component_fields(data):
    if data.get("is_component_step") and not data.get("is_component"):
        raise ValidationError({"is_component": [strings.Goods.FORM_NO_COMPONENT_SELECTED]})

    # Validate component detail field if the answer was not 'No'
    if data.get("is_component") and data["is_component"] not in [Component.NO, "None"]:
        valid_components = validate_component_details(data)
        if not valid_components["is_valid"]:
            raise ValidationError({valid_components["details_field"]: [valid_components["error"]]})

        data["component_details"] = data[valid_components["details_field"]]


def validate_information_security_field(data):
    if data.get("is_information_security_step") and data.get("uses_information_security") is None:
        raise ValidationError(
            {"uses_information_security": [strings.Goods.FORM_PRODUCT_DESIGNED_FOR_SECURITY_FEATURES]}
        )
