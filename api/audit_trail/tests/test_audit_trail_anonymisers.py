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
        "case_officer": "Dr. Leanne Smith",
        "destination_name": "Gail Morgan",
        "ecju_query": "At saepe quae. A laudantium sint doloribus eveniet sit "
        "deleniti necessitatibus. Rem consequuntur molestiae at "
        "voluptatibus. Voluptatum laudantium error enim commodi ex "
        "ullam. Vitae nobis nesciunt ipsam nisi. Et doloribus delectus "
        "reprehenderit alias voluptatem.",
        "ecju_response": "Architecto perspiciatis consectetur corrupti aliquam "
        "aspernatur praesentium. Placeat saepe minima maxime "
        "doloremque dolor perspiciatis. Neque iste optio voluptatum "
        "totam recusandae. Eveniet beatae nesciunt excepturi.",
        "email": "dixondonna@thompson-pickering.com",
        "file_name": "ea.key",
        "firstname": "Chloe",
        "lastname": "Smith",
        "mention_users": ["Dr. Gerard Poole", "Garry Sutton-Richardson"],
        "new": "Jodie Saunders",
        "new_end_use_detail": "Ratione culpa cum minus. Nisi ipsam cupiditate iusto.",
        "old": "Conor Metcalfe",
        "old_end_use_detail": "Quibusdam repudiandae aspernatur nisi praesentium cum. "
        "Odit fugiat soluta necessitatibus impedit.",
        "organisation_name": "Jones Group",
        "party_name": "Dawn Leonard",
        "removed_user_name": "Dr. Martin Warren",
        "site_name": "Deborah Williams",
        "unchanged": "unchanged value",
        "user": "Dr. Oliver Davey",
    }
