import json

from faker import Faker

from django_db_anonymiser.db_anonymiser import faker as db_anonymiser_sanitizers

fake = Faker("en-GB")


def sanitize_application(value):
    application = json.loads(value)
    user_items = application.get("sections", {}).get("user_information", {}).get("items", [])
    if not user_items:
        return application
    for item in user_items:
        address = item["fields"]["address"]["raw_answer"]
        sanitized_address = db_anonymiser_sanitizers.sanitize_address(address)
        item["fields"]["address"]["raw_answer"] = sanitized_address
        item["fields"]["address"]["answer"] = sanitized_address
        full_name = item["fields"]["end_user_name"]["answer"]
        sanitized_name = db_anonymiser_sanitizers.sanitize_name(full_name)
        item["fields"]["end_user_name"]["raw_answer"] = sanitized_name
        item["fields"]["end_user_name"]["answer"] = sanitized_name
    return json.dumps(application)
