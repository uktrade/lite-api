import json

from faker import Faker

from django_db_anonymiser.db_anonymiser import faker as db_anonymiser_sanitizers

fake = Faker("en-GB")


def _set_answer(field, answer):
    field["answer"] = answer
    field["raw_answer"] = answer


def _set_field_answers(field_path, sanitizer_function, application):
    path_parts = field_path.split(".")
    field = application
    for path in path_parts:
        field = field.get(path, {})
    if not field:
        return
    sanitized_value = sanitizer_function(field["answer"])
    _set_answer(field, sanitized_value)


def sanitize_user_information(application):
    user_items = application.get("sections", {}).get("user_information", {}).get("items", [])
    for item in user_items:
        address_field = item["fields"]["address"]
        address = address_field["raw_answer"]
        sanitized_address = db_anonymiser_sanitizers.sanitize_address(address)
        _set_answer(address_field, sanitized_address)

        full_name_field = item["fields"]["end_user_name"]
        full_name = full_name_field["answer"]
        sanitized_name = db_anonymiser_sanitizers.sanitize_name(full_name)
        _set_answer(full_name_field, sanitized_name)


def sanitize_application(value):
    application = json.loads(value)
    sanitize_config = {
        "sections.general_application_details.fields.previous_application_details": db_anonymiser_sanitizers.sanitize_text,
        "sections.approval_type.fields.approval_details_text": db_anonymiser_sanitizers.sanitize_text,
        "sections.product_information.fields.product_name": db_anonymiser_sanitizers.sanitize_text,
        "sections.product_information.fields.product_description": db_anonymiser_sanitizers.sanitize_text,
        "sections.product_information.fields.issuing_authority_name_address": db_anonymiser_sanitizers.sanitize_address,
        "sections.product_information.fields.cryptography_or_security_feature_info": db_anonymiser_sanitizers.sanitize_text,
        "sections.product_information.fields.full_name": db_anonymiser_sanitizers.sanitize_name,
        "sections.product_information.fields.address": db_anonymiser_sanitizers.sanitize_address,
        "sections.product_information.fields.phone_number": db_anonymiser_sanitizers.sanitize_phone_number,
        "sections.product_information.fields.email_address": db_anonymiser_sanitizers.sanitize_email,
        "sections.product_information.fields.used_by_uk_armed_forces_info": db_anonymiser_sanitizers.sanitize_text,
    }

    for path, sanitizer_function in sanitize_config.items():
        _set_field_answers(path, sanitizer_function, application)
    sanitize_user_information(application)
    return json.dumps(application)
