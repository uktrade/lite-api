from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from conf.exceptions import BadRequestError
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


def validate_identification_markings(validated_data):
    """ Mandatory question for firearm goods (Group 2) with conditional details fields based on the answer """
    has_identification_markings = validated_data.get("has_identification_markings")
    if "has_identification_markings" in validated_data and has_identification_markings is None:
        raise serializers.ValidationError({"has_identification_markings": [strings.Goods.FIREARM_GOOD_NO_MARKINGS]})

    if has_identification_markings is True and not validated_data.get("identification_markings_details"):
        raise serializers.ValidationError(
            {"identification_markings_details": [strings.Goods.FIREARM_GOOD_NO_DETAILS_ON_MARKINGS]}
        )

    if has_identification_markings is False and not validated_data.get("no_identification_markings_details"):
        raise serializers.ValidationError(
            {"no_identification_markings_details": [strings.Goods.FIREARM_GOOD_NO_DETAILS_ON_NO_MARKINGS]}
        )


def validate_section_certificate_number_and_expiry_date(validated_data):
    date_of_expiry = validated_data.get("section_certificate_date_of_expiry")

    # Section certificate number and date of expiry are mandatory
    if not validated_data.get("section_certificate_number"):
        raise serializers.ValidationError({"section_certificate_number": strings.Goods.FIREARM_GOOD_NO_CERT_NUM})
    if not date_of_expiry:
        raise serializers.ValidationError(
            {"section_certificate_date_of_expiry": strings.Goods.FIREARM_GOOD_NO_EXPIRY_DATE}
        )

    # Date of expiry has to be in the future
    if date_of_expiry and date_of_expiry < timezone.now().date():
        raise serializers.ValidationError(
            {"section_certificate_date_of_expiry": [strings.Goods.FIREARM_GOOD_INVALID_EXPIRY_DATE]}
        )


def check_if_firearm_details_edited_on_unsupported_good(data):
    """ Return bad request if editing any of the firearm details on a good that is not in group 2 firearms """
    firearm_good_specific_details = [
        "type",
        "year_of_manufacture",
        "calibre",
        "is_covered_by_firearm_act_section_one_two_or_five",
        "section_certificate_number",
        "section_certificate_date_of_expiry",
        "has_identification_markings",
        "identification_markings_details",
        "no_identification_markings_details",
    ]
    if any(detail in data["firearm_details"] for detail in firearm_good_specific_details):
        raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})


def check_if_unsupported_fields_edited_on_firearm_good(data):
    """
    Return bad request if trying to edit any details that are NOT applicable to category 2 firearm goods.
    This includes all military use/component/information security fields only relevant to category 1
    along with the software or technology details for category 3
    """
    sections = [
        "is_military_use",
        "modified_military_use_details",
        "is_component",
        "designed_details",
        "modified_details",
        "general_details",
        "uses_information_security",
        "information_security_details",
        "software_or_technology_details",
    ]
    # The parent field values don't get sent if not explicitly selected on the form, so we check the presence of details fields as well
    if any(section in data for section in sections):
        raise BadRequestError({"non_field_errors": [strings.Goods.CANNOT_SET_DETAILS_ERROR]})
