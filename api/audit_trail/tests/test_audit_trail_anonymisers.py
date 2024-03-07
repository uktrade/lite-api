import json

import pytest
from faker import Faker

from api.audit_trail.audit_trail_anonymisers import sanitize_payload


# NOTE: Force faker to use a seed when producing output so that we can assume a
# deterministic set of results
@pytest.fixture(autouse=True)
def seed_faker():
    Faker.seed(0)


def test_sanitize_payload():
    payload = {
        "case_officer": "some case officer",
        "party_name": "some party name",
        "organisation_name": "some organisation name",
        "user": "some user",
        "firstname": "some first",
        "lastname": "some last",
        "mention_users": ["some user", "some other user"],
        "site_name": "some site",
        "destination_name": "some destination",
        "file_name": "some.file.txt",
        "ecju_query": "some query",
        "ecju_response": "some response",
        "email": "some.email@example.net",
        "removed_user_name": "some name",
        "new_end_use_detail": "some detail",
        "old_end_use_detail": "some old detail",
        "new": "some new",
        "old": "some old",
        "unchanged": "unchanged value",
    }
    sanitized_payload = sanitize_payload(json.dumps(payload))
    assert json.loads(sanitized_payload) == {
        "case_officer": "Dr Rhys Thomas",
        "destination_name": "Amelia Sheppard",
        "ecju_query": "Nostrum totam vitae labore sint ea. Totam at saepe quae quos numquam nostrum. Doloribus eveniet sit deleniti necessitatibus dolores. Rem ipsum aspernatur eum. Voluptatum laudantium error enim commodi ex ullam.",
        "ecju_response": "Molestias enim at reiciendis et doloribus delectus reprehenderit. Nostrum omnis labore. Perspiciatis consectetur corrupti aliquam. Tempore unde molestiae hic.",
        "email": "zoe33@example.net",
        "file_name": "consequuntur.docx",
        "firstname": "Bradley",
        "lastname": "Davey",
        "mention_users": ["Malcolm Scott", "Jay Barker"],
        "new": "Dr Sally Harper",
        "new_end_use_detail": "Ratione culpa cum minus. Nisi ipsam cupiditate iusto.",
        "old": "Susan Robinson",
        "old_end_use_detail": "Quibusdam repudiandae aspernatur nisi praesentium cum. "
        "Odit fugiat soluta necessitatibus impedit.",
        "organisation_name": "Evans-Norman",
        "party_name": "Jones, Bell and Burke",
        "removed_user_name": "Rhys Jackson",
        "site_name": "Denise Gibson",
        "unchanged": "unchanged value",
        "user": "Tina Khan",
    }
