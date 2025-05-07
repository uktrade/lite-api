import json


from api.f680.f680_anonymisers import sanitize_application
from .f680_test_data import APPLICATION_JSON


def test_sanitize_application_empty_dict():
    assert sanitize_application('{"key": "val"}') == '{"key": "val"}'


def _get_field(application, path):
    path_parts = path.split(".")
    field = application
    for path in path_parts:
        field = field.get(path, {})
    return field


def _assert_sanitized(original_application, sanitized_application, path):
    original_field = _get_field(original_application, path)
    sanitized_field = _get_field(sanitized_application, path)

    assert "answer" in sanitized_field.keys()
    assert "raw_answer" in sanitized_field.keys()
    assert "answer" in original_field.keys()
    assert "raw_answer" in original_field.keys()

    assert sanitized_field["answer"] != original_field["answer"]
    assert sanitized_field["raw_answer"] != original_field["raw_answer"]


def test_sanitize_application():
    sanitized_json = sanitize_application(json.dumps(APPLICATION_JSON))
    sanitized_application = json.loads(sanitized_json)

    _assert_sanitized(
        APPLICATION_JSON,
        sanitized_application,
        "sections.general_application_details.fields.previous_application_details",
    )
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.approval_type.fields.approval_details_text")
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.product_information.fields.product_name")
    _assert_sanitized(
        APPLICATION_JSON, sanitized_application, "sections.product_information.fields.product_description"
    )
    _assert_sanitized(
        APPLICATION_JSON, sanitized_application, "sections.product_information.fields.issuing_authority_name_address"
    )
    _assert_sanitized(
        APPLICATION_JSON,
        sanitized_application,
        "sections.product_information.fields.cryptography_or_security_feature_info",
    )
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.product_information.fields.full_name")
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.product_information.fields.address")
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.product_information.fields.phone_number")
    _assert_sanitized(APPLICATION_JSON, sanitized_application, "sections.product_information.fields.email_address")
    _assert_sanitized(
        APPLICATION_JSON, sanitized_application, "sections.product_information.fields.used_by_uk_armed_forces_info"
    )
    zipped_user_items = zip(
        APPLICATION_JSON["sections"]["user_information"]["items"],
        sanitized_application["sections"]["user_information"]["items"],
    )
    for original_user_item, sanitized_user_item in zipped_user_items:
        assert original_user_item["id"] == sanitized_user_item["id"]
        _assert_sanitized(original_user_item, sanitized_user_item, "fields.address")
        _assert_sanitized(original_user_item, sanitized_user_item, "fields.end_user_name")
        _assert_sanitized(original_user_item, sanitized_user_item, "fields.end_user_intended_end_use")
