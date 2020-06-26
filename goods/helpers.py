from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from goods.enums import Component, MilitaryUse
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

    if not data.get(field):
        return {"is_valid": False, "details_field": field, "error": error}
    if len(data.get(field)) > 2000:
        return {"is_valid": False, "details_field": field, "error": strings.Goods.COMPONENT_DETAILS_OVER_LIMIT_ERROR}
    return {"is_valid": True, "details_field": field}


def validate_military_use(data):
    """ Validate military use selected if category is either Group 1 or 3. """
    if "item_category" in data and not data.get("is_military_use"):
        raise ValidationError({"is_military_use": [strings.Goods.FORM_NO_MILITARY_USE_SELECTED]})

    is_military_use = data.get("is_military_use")
    if is_military_use == MilitaryUse.YES_MODIFIED and not data.get("modified_military_use_details"):
        raise serializers.ValidationError({"modified_military_use_details": [strings.Goods.NO_MODIFICATIONS_DETAILS]})
