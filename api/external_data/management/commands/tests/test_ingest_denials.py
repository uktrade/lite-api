import pytest
from unittest import mock

from django.core.management import call_command

from api.external_data.management.commands import ingest_denials
from api.external_data.models import Denial
from rest_framework.exceptions import ValidationError
import json
import io


@pytest.mark.elasticsearch
@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials(mock_json_content, mock_delete_file):
    mock_json_content.return_value = {
        "Body": io.StringIO(
            json.dumps(
                [
                    {
                        "reference": "DN001\/0003",
                        "regime_reg_ref": "12",
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
                        "regime_reg_ref": "123",
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
                        "regime_reg_ref": "1234",
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
            )
        )
    }

    call_command("ingest_denials", "json_file", rebuild=True)
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
    assert denial_record.regime_reg_ref == "12"

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.elasticsearch
@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_validation_call(mock_json_content, mock_delete_file):
    mock_json_content.return_value = {
        "Body": io.StringIO(
            json.dumps(
                [
                    {
                        "name": "fail",
                    },
                ]
            )
        )
    }

    with pytest.raises(ValidationError):
        call_command("ingest_denials", "json_file")

    assert not Denial.objects.all().exists()

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
def test_populate_denials_raise_exception_with_existing_records(mock_delete_file):
    Denial(reference="dummy").save()
    with pytest.raises(Exception):
        call_command("ingest_denials", "json_file")

    assert Denial.objects.all().count() == 1
    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")
