import pytest

from api.external_data.helpers import get_denial_entity_type


@pytest.mark.parametrize(
    "data,expected",
    (
        ({"end_user_flag": "true", "consignee_flag": "false", "other_role": "false"}, "End-user"),
        ({"end_user_flag": "false", "consignee_flag": "true", "other_role": "false"}, "Consignee"),
        ({"end_user_flag": "false", "consignee_flag": "false", "other_role": "true"}, "Third-party"),
        ({"other_role": "true"}, "Third-party"),
        ({"end_user_flag": "true"}, "End-user"),
        ({"consignee_flag": "true"}, "Consignee"),
        ({}, ""),
    ),
)
def test_get_denial_entity_type(data, expected):
    assert get_denial_entity_type(data) == expected
