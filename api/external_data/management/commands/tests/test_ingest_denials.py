from api.applications.tests.factories import DenialMatchFactory
import pytest
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError

from api.external_data.management.commands import ingest_denials
from api.external_data.models import NewDenial, DenialEntity

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
                        "item_list_codes": "123456",
                        "item_description": "phone",
                        "end_use": "locating phone",
                        "end_user_flag": "true",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason a",
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
                        "reference": "DN001\/0001",
                        "regime_reg_ref": "1234",
                        "name": "Test3 case",
                        "address": "antartica",
                        "notifying_government": "United States",
                        "country": "Italy",
                        "item_description": "lazer",
                        "end_use": "testing",
                        "end_user_flag": "false",
                        "consignee_flag": "false",
                        "reason_for_refusal": "reason c",
                    },
                ]
            )
        )
    }


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials(mock_json_content, mock_delete_file, json_file_data):
    mock_json_content.return_value = json_file_data

    call_command("ingest_denials", "json_file", rebuild=True)
    assert NewDenial.objects.all().count() == 3
    denial_record = NewDenial.objects.all()[0]
    assert denial_record.reference == "DN001\/0003"

    assert denial_record.notifying_government == "United Kingdom"

    assert denial_record.item_list_codes == "123456"
    assert denial_record.item_description == "phone"
    assert denial_record.end_use == "locating phone"
    assert denial_record.regime_reg_ref == "12"
    assert denial_record.reason_for_refusal == "reason a"

    entity_record = denial_record.denial_entity.first()
    assert entity_record.name == "Test1 case"
    assert entity_record.address == "somewhere\nmid\nlatter\nCairo"
    assert entity_record.country == "United States"
    assert entity_record.type == "End-user"

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_duplicates(mock_json_content, mock_delete_file):
    json_file_data = {
        "Body": io.StringIO(
            json.dumps(
                [
                    {
                        "reference": "DN001\/0003",
                        "regime_reg_ref": "12",
                        "notifying_government": "United Kingdom",
                        "item_list_codes": "123456",
                        "item_description": "phone",
                        "end_use": "locating phone",
                        "end_user_flag": "true",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason a",
                    },
                    {
                        "reference": "DN001\/0003",
                        "regime_reg_ref": "12",
                        "notifying_government": "United Kingdom",
                        "item_list_codes": "123456",
                        "item_description": "phone",
                        "end_use": "locating phone",
                        "end_user_flag": "true",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason a",
                    },
                ]
            )
        )
    }
    mock_json_content.return_value = json_file_data

    call_command("ingest_denials", "json_file", rebuild=True)
    assert NewDenial.objects.all().count() == 1
    assert DenialEntity.objects.all().count() == 1

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_row_error(mock_json_content, mock_delete_file):
    json_file_data = {
        "Body": io.StringIO(
            json.dumps(
                [
                    {
                        "reference": "DN001\/0003",
                        "regime_reg_ref": "12",
                        "notifying_government": "United Kingdom",
                        "item_list_codes": "123456",
                        "item_description": "phone",
                        "end_use": "locating phone",
                        "end_user_flag": "true",
                        "consignee_flag": "true",
                        "reason_for_refusal": "reason a",
                    },
                    {
                        "reference": "DN001\/0003",
                        "regime_reg_ref": None,
                        "notifying_government": "United Kingdom",
                    },
                ]
            )
        )
    }
    mock_json_content.return_value = json_file_data
    with pytest.raises(IntegrityError):
        call_command("ingest_denials", "json_file", rebuild=True)
    assert not NewDenial.objects.all().exists()
    assert not DenialEntity.objects.all().exists()

    mock_delete_file.assert_called_with(document_id="json_file", s3_key="json_file")


@pytest.mark.django_db
@mock.patch.object(ingest_denials.s3_operations, "delete_file")
@mock.patch.object(ingest_denials.s3_operations, "get_object")
def test_populate_denials_with_no_data_in_file(mock_get_file, mock_delete_file):
    mock_get_file.return_value = {"Body": io.StringIO(json.dumps([]))}
    DenialMatchFactory()

    call_command("ingest_denials", "json_file")

    assert not NewDenial.objects.all().exists()
    assert not DenialEntity.objects.all().exists()
