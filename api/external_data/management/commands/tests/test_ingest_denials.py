from api.applications.tests.factories import (
    DenialEntityFactory,
    DenialFactory,
    DenialMatchOnApplicationFactory,
    StandardApplicationFactory,
)
import pytest
from unittest import mock

from django.core.management import call_command

from api.external_data.management.commands import ingest_denials
from api.external_data.models import DenialEntity
from rest_framework.exceptions import ValidationError
import json
import io


@pytest.fixture
def json_file_data():
    return {
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
                        "denial_cle": "123456",
                        "item_description": "phone",
                        "end_use": "locating phone",
                        "end_user_flag": "true",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason a",
                        "spire_entity_id": 1234,
                    },
                    {
                        "reference": "DN001\/0002",
                        "regime_reg_ref": "123",
                        "name": "Test2 case",
                        "address": "no address given",
                        "notifying_government": "Germany",
                        "country": "France",
                        "denial_cle": "12345\/2009",
                        "item_description": "testing machine",
                        "end_use": "For teaching purposes",
                        "end_user_flag": "false",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason b",
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
                        "reason_for_refusal": "reason c",
                    },
                    {
                        "reference": "DN001\/0000",
                        "regime_reg_ref": "12345",
                        "name": "Test4 case",
                        "address": "antartica",
                        "notifying_government": "United States",
                        "country": "Italy",
                        "item_description": "lazer",
                        "end_use": "testing",
                        "end_user_flag": "false",
                        "consignee_flag": "false",
                        "other_role": "my role",
                        "reason_for_refusal": "reason c",
                    },
                ]
            )
        )
    }


@pytest.mark.elasticsearch
@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials(mock_json_content, mock_delete_file, json_file_data):
    mock_json_content.return_value = json_file_data

    call_command("ingest_denials", "json_file", rebuild=True)
    assert DenialEntity.objects.all().count() == 4
    denial_record = DenialEntity.objects.all()[0]
    assert denial_record.denial.reference == "DN001\/0003"
    assert denial_record.name == "Test1 case"
    assert denial_record.address == "somewhere\nmid\nlatter\nCairo"
    assert denial_record.denial.notifying_government == "United Kingdom"
    assert denial_record.country == "United States"
    assert denial_record.denial.denial_cle == "123456"
    assert denial_record.denial.item_description == "phone"
    assert denial_record.denial.end_use == "locating phone"
    assert denial_record.denial.regime_reg_ref == "12"
    assert denial_record.denial.reason_for_refusal == "reason a"

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

    assert not DenialEntity.objects.all().exists()

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_with_existing_matching_records(mock_get_file, mock_delete_file, json_file_data):
    mock_get_file.return_value = json_file_data
    case = StandardApplicationFactory()

    denial_enity = DenialEntityFactory(denial=DenialFactory(regime_reg_ref="12"), name="Test1 case")
    DenialMatchOnApplicationFactory(application=case, category="exact", denial_entity=denial_enity)

    call_command("ingest_denials", "json_file")

    assert DenialEntity.objects.all().count() == 4


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_with_no_data_in_file(mock_get_file, mock_delete_file):
    mock_get_file.return_value = {"Body": io.StringIO(json.dumps([]))}
    DenialEntityFactory()

    call_command("ingest_denials", "json_file")

    assert DenialEntity.objects.all().count() == 1
