from rest_framework.exceptions import ValidationError

from goods.enums import Component, ItemCategory
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
    if len(data[field]) > 2000:
        return {"is_valid": False, "details_field": field, "error": strings.Goods.COMPONENT_DETAILS_OVER_LIMIT_ERROR}
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


def validate_software_or_technology_details(data):
    """ Validate software/technology details field if the item category is software or technology. """
    if "item_category" in data and data["item_category"] in [
        ItemCategory.GROUP3_SOFTWARE,
        ItemCategory.GROUP3_TECHNOLOGY,
    ]:
        if not data.get("software_or_technology_details"):
            raise ValidationError(
                {
                    "software_or_technology_details": [
                        strings.Goods.FORM_NO_SOFTWARE_DETAILS
                        if data["item_category"] == ItemCategory.GROUP3_SOFTWARE
                        else strings.Goods.FORM_NO_TECHNOLOGY_DETAILS
                    ]
                }
            )


def validate_military_use(data):
    """ Validate military use selected if category is either Group 1 or 3. """
    if "item_category" in data and data["item_category"] not in [
        ItemCategory.GROUP2_FIREARMS,
    ]:
        if not data.get("is_military_use"):
            raise ValidationError({"is_military_use": [strings.Goods.FORM_NO_MILITARY_USE_SELECTED]})
