import pytest
from unittest import mock

from django.core.management import call_command

from api.external_data.management.commands import ingest_denials
from api.external_data.models import Denial
from rest_framework.exceptions import ValidationError


@pytest.mark.elasticsearch
@pytest.mark.django_db
@mock.patch.object(ingest_denials, "get_json_content")
def test_populate_denials(mock_json_content):
    mock_json_content.return_value = [
        {
            "reference": "DN001\/0003",
            "name": "Test1 case",
            "address": "somewhere\nmid\nlatter\nCairo",
            "notifying_government": "United Kingdom",
            "country": "United States",
            "item_list_codes": "123456",
            "item_description": "phone",
            "end_use": "locating phone",
            "end_user_flag": "true",
            "consignee_flag": "true",
        },
        {
            "reference": "DN001\/0002",
            "name": "Test2 case",
            "address": "no address given",
            "notifying_government": "Germany",
            "country": "France",
            "item_list_codes": "12345\/2009",
            "item_description": "testing machine",
            "end_use": "For teaching purposes",
            "end_user_flag": "true",
            "consignee_flag": "true",
        },
        {
            "reference": "DN001\/0001",
            "name": "Test3 case",
            "address": "antartica",
            "notifying_government": "United States",
            "country": "Italy",
            "item_description": "lazer",
            "end_use": "testing",
            "end_user_flag": "true",
            "consignee_flag": "false",
        },
    ]
    call_command("ingest_denials", rebuild=True)
    assert Denial.objects.all().count() == 3
    denial_record = Denial.objects.all()[0]
    assert denial_record.reference == "DN001\/0003"
    assert denial_record.name == "Test1 case"
    assert denial_record.address == "somewhere\nmid\nlatter\nCairo"
    assert denial_record.notifying_government == "United Kingdom"
    assert denial_record.country == "United States"
    assert denial_record.item_list_codes == "123456"
    assert denial_record.item_description == "phone"
    assert denial_record.end_use == "locating phone"


@pytest.mark.elasticsearch
@pytest.mark.django_db
@mock.patch.object(ingest_denials, "get_json_content")
def test_populate_denials_validation_call(mock_json_content):
    mock_json_content.return_value = [
        {
            "name": "fail",
        },
    ]

    with pytest.raises(ValidationError):
        call_command("ingest_denials", rebuild=True)
    assert Denial.objects.all().count() == 0
