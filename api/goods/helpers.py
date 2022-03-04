from django.utils import timezone
from rest_framework import serializers

from api.core.exceptions import BadRequestError
from api.organisations.models import DocumentOnOrganisation
from api.organisations.enums import OrganisationDocumentType
from lite_content.lite_api import strings

FIREARMS_CORE_TYPES = ["firearms", "ammunition", "components_for_firearms", "components_for_ammunition"]
FIREARMS_ACCESSORY = ["firearms_accessory"]


def validate_firearms_act_certificate(validated_data):
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
        "serial_numbers_available",
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
