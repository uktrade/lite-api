from copy import deepcopy
import json

import pytest

from faker import Faker

from api.f680.f680_anonymisers import sanitize_application
from .f680_test_data import APPLICATION_JSON


# NOTE: Force faker to use a seed when producing output so that we can assume a
# deterministic set of results
@pytest.fixture(autouse=True)
def seed_faker():
    Faker.seed(0)


def test_sanitize_application_empty_dict():
    assert sanitize_application('{"key": "val"}') == '{"key": "val"}'


def test_sanitize_application():
    expected_data = deepcopy(APPLICATION_JSON)
    expected_user_information = expected_data["sections"]["user_information"]["items"]

    address_1 = "Flat 4, Gibbons tunnel, Lesleystad, L8C 2EZ"  # /PS-IGNORE
    end_user_name_1 = "Dr Vincent Robinson"
    expected_user_information[0]["fields"]["address"]["raw_answer"] = address_1
    expected_user_information[0]["fields"]["address"]["answer"] = address_1
    expected_user_information[0]["fields"]["end_user_name"]["raw_answer"] = end_user_name_1
    expected_user_information[0]["fields"]["end_user_name"]["answer"] = end_user_name_1

    address_2 = "Flat 1, Jones courts, Tracymouth, L8H 8LB"  # /PS-IGNORE
    end_user_name_2 = "Mr Jordan Peters"
    expected_user_information[1]["fields"]["address"]["raw_answer"] = address_2
    expected_user_information[1]["fields"]["address"]["answer"] = address_2
    expected_user_information[1]["fields"]["end_user_name"]["raw_answer"] = end_user_name_2
    expected_user_information[1]["fields"]["end_user_name"]["answer"] = end_user_name_2

    address_3 = "753 Campbell circles, New Ross, G87 1PW"  # /PS-IGNORE
    end_user_name_3 = "Alexander Atkins"
    expected_user_information[2]["fields"]["address"]["raw_answer"] = address_3
    expected_user_information[2]["fields"]["address"]["answer"] = address_3
    expected_user_information[2]["fields"]["end_user_name"]["raw_answer"] = end_user_name_3
    expected_user_information[2]["fields"]["end_user_name"]["answer"] = end_user_name_3

    sanitized_json = sanitize_application(json.dumps(APPLICATION_JSON))
    assert sanitized_json == json.dumps(expected_data)
