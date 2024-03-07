import json

from faker import Faker

from django_db_anonymiser.db_anonymiser import faker as db_anonymiser_sanitizers

fake = Faker("en-GB")


def sanitize_mention_users(users):
    sanitized_users = []
    for user in users:
        sanitized_users.append(fake.name())
    return sanitized_users


ALL_SANITIZERS = {
    "case_officer": db_anonymiser_sanitizers.sanitize_name,
    "party_name": db_anonymiser_sanitizers.sanitize_company_name,
    "organisation_name": db_anonymiser_sanitizers.sanitize_company_name,
    "user": db_anonymiser_sanitizers.sanitize_name,
    "firstname": db_anonymiser_sanitizers.sanitize_first_name,
    "lastname": db_anonymiser_sanitizers.sanitize_last_name,
    "mention_users": sanitize_mention_users,
    "site_name": db_anonymiser_sanitizers.sanitize_name,
    "destination_name": db_anonymiser_sanitizers.sanitize_name,
    "file_name": db_anonymiser_sanitizers.sanitize_filename,
    "ecju_query": db_anonymiser_sanitizers.sanitize_text,
    "ecju_response": db_anonymiser_sanitizers.sanitize_text,
    "email": db_anonymiser_sanitizers.sanitize_email,
    "removed_user_name": db_anonymiser_sanitizers.sanitize_name,
    "new_end_use_detail": db_anonymiser_sanitizers.sanitize_short_text,
    "old_end_use_detail": db_anonymiser_sanitizers.sanitize_short_text,
    "new": db_anonymiser_sanitizers.sanitize_name,
    "old": db_anonymiser_sanitizers.sanitize_name,
}


def sanitize_payload(value):
    payload = json.loads(value)
    for key_to_sanitize, sanitizer in ALL_SANITIZERS.items():
        if key_to_sanitize in payload:
            payload[key_to_sanitize] = sanitizer(payload[key_to_sanitize])
    return json.dumps(payload)
