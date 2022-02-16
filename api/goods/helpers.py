from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.core.exceptions import BadRequestError
from api.goods.enums import Component, MilitaryUse
from api.goods.models import FirearmGoodDetails
from api.organisations.models import DocumentOnOrganisation
from api.organisations.enums import OrganisationDocumentType
from lite_content.lite_api import strings

FIREARMS_CORE_TYPES = ["firearms", "ammunition", "components_for_firearms", "components_for_ammunition"]
FIREARMS_ACCESSORY = ["firearms_accessory"]


def validate_component_details(data):
    """Validate the accompanying details for the chosen 'yes' component option."""

    if "firearm_details" in data and data["firearm_details"].get("type") not in FIREARMS_ACCESSORY:
        return

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
    """Validate military use selected if category is either Group 1, 2 or 3."""
    if "firearm_details" in data and data["firearm_details"].get("type") in FIREARMS_CORE_TYPES:
        return

    if "item_category" in data and not data.get("is_military_use"):
        raise ValidationError({"is_military_use": [strings.Goods.FORM_NO_MILITARY_USE_SELECTED]})

    is_military_use = data.get("is_military_use")
    if is_military_use == MilitaryUse.YES_MODIFIED and not data.get("modified_military_use_details"):
        raise serializers.ValidationError({"modified_military_use_details": [strings.Goods.NO_MODIFICATIONS_DETAILS]})


def validate_information_security(data):
    if "firearm_details" in data and data["firearm_details"].get("type") in FIREARMS_CORE_TYPES:
        return

    if "uses_information_security" in data and data.get("uses_information_security") is None:
        raise serializers.ValidationError(
            {"uses_information_security": [strings.Goods.FORM_PRODUCT_DESIGNED_FOR_SECURITY_FEATURES]}
        )


def validate_identification_markings(validated_data):
    if "type" in validated_data and validated_data.get("type") not in FIREARMS_CORE_TYPES:
        return

    number_of_items = validated_data.get("number_of_items")
    if "number_of_items" in validated_data and (number_of_items <= 0 or number_of_items == None):
        raise serializers.ValidationError({"number_of_items": "Enter the number of items"})

    # Mandatory question for firearm goods (Group 2) with conditional details fields based on the answer
    has_identification_markings = validated_data.get("has_identification_markings")
    if "has_identification_markings" in validated_data and has_identification_markings is None:
        raise serializers.ValidationError({"has_identification_markings": [strings.Goods.FIREARM_GOOD_NO_MARKINGS]})

    if has_identification_markings is False and not validated_data.get("no_identification_markings_details"):
        raise serializers.ValidationError(
            {"no_identification_markings_details": ["Enter a reason why the product has not been marked"]}
        )

    serial_numbers_available = validated_data.get("serial_numbers_available")
    if serial_numbers_available == FirearmGoodDetails.SN_NOT_AVAILABLE and not validated_data.get(
        "no_serial_numbers_reason"
    ):
        raise serializers.ValidationError(
            {"no_serial_numbers_reason": ["Enter a reason why the product has not been marked"]}
        )

    serial_numbers = validated_data.get("serial_numbers")
    if "serial_numbers" in validated_data and has_identification_markings:
        is_missing_all_serial_numbers = all(not serial_number for serial_number in serial_numbers)
        if is_missing_all_serial_numbers:
            raise serializers.ValidationError({"serial_numbers": "Enter at least one serial number"})


def validate_firearms_act_section(validated_data):
    errors = {}

    if "type" in validated_data and validated_data.get("type") not in FIREARMS_CORE_TYPES:
        return

    covered_by_firearms_act = validated_data.get("is_covered_by_firearm_act_section_one_two_or_five", "")
    selected_section = validated_data.get("firearms_act_section", "")

    if covered_by_firearms_act == "":
        errors["is_covered_by_firearm_act_section_one_two_or_five"] = strings.Goods.FIREARM_GOOD_NO_SECTION

    if covered_by_firearms_act == "Yes" and selected_section == "":
        errors["firearms_act_section"] = "Select which section the product is covered by"

    if errors:
        raise serializers.ValidationError(errors)


def validate_firearms_act_certificate_expiry_date(validated_data):
    errors = {}

    if "type" in validated_data and validated_data.get("type") not in FIREARMS_CORE_TYPES:
        return

    covered_by_firearms_act = validated_data.get("is_covered_by_firearm_act_section_one_two_or_five", "")
    if covered_by_firearms_act == "No" or covered_by_firearms_act == "Unsure":
        return

    certificate_missing = validated_data.get("section_certificate_missing", False) == True
    if certificate_missing:
        if validated_data.get("section_certificate_missing_reason", "") == "":
            errors["section_certificate_missing_reason"] = "Enter a reason why you do not have a section 1 certificate"
    else:
        # Section certificate number and date of expiry are mandatory
        if validated_data.get("section_certificate_number") == "":
            errors["section_certificate_number"] = "Enter the certificate number"

        date_of_expiry = validated_data.get("section_certificate_date_of_expiry")
        if not date_of_expiry:
            errors[
                "section_certificate_date_of_expiry"
            ] = "Enter the certificate expiry date and include a day, month and year"

        # Date of expiry has to be in the future
        if date_of_expiry and date_of_expiry < timezone.now().date():
            errors["section_certificate_date_of_expiry"] = strings.Goods.FIREARM_GOOD_INVALID_EXPIRY_DATE

    if errors:
        raise serializers.ValidationError(errors)


def check_if_firearm_details_edited_on_unsupported_good(data):
    """Return bad request if editing any of the firearm details on a good that is not in group 2 firearms"""
    firearm_good_specific_details = [
        "type",
        "year_of_manufacture",
        "calibre",
        "is_covered_by_firearm_act_section_one_two_or_five",
        "section_certificate_number",
        "section_certificate_date_of_expiry",
        "has_identification_markings",
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


def has_valid_certificate(organisation_id, document_type):
    certificate_exists = DocumentOnOrganisation.objects.filter(
        organisation=organisation_id,
        document_type=document_type,
    ).first()

    if certificate_exists and timezone.now().date() < certificate_exists.expiry_date:
        return True

    return False


def update_firearms_certificate_data(organisation_id, firearm_data):
    has_valid_rfd = has_valid_certificate(
        organisation_id, OrganisationDocumentType.REGISTERED_FIREARM_DEALER_CERTIFICATE
    )
    has_valid_section5 = has_valid_certificate(organisation_id, OrganisationDocumentType.FIREARM_SECTION_FIVE)

    if not has_valid_rfd:
        if has_valid_section5:
            del firearm_data["section_certificate_number"]
        return firearm_data

    if has_valid_rfd and has_valid_section5:
        # because user is not asked to upload the certificate again
        # it fails validation if this is not removed here
        del firearm_data["section_certificate_number"]

    return firearm_data
