import json

from rest_framework import serializers
from rest_framework import status

from api.goods.libraries.save_good import flatten_errors, create_or_update_good


def test_flatten_errors():
    data = {
        "pv_grading_details": {"example_field1": "Invalid value",},
        "firearm_details": {
            "example_field2": "Invalid value",
            "document_on_organisation": {"example_field3": "Invalid value",},
        },
    }
    json = {
        "pv_grading_details": {"example_field1": ["Example error 1"]},
        "firearm_details": {
            "example_field2": ["Example error 2"],
            "document_on_organisation": {"example_field3": ["Example error 3"],},
        },
    }
    expected = {
        "example_field1": ["Example error 1"],
        "example_field2": ["Example error 2"],
        "example_field3": ["Example error 3"],
    }
    assert flatten_errors(json, data) == expected


def test_flatten_errors_certificate_error():
    data = {
        "pv_grading_details": {"example_field1": "Invalid value",},
        "firearm_details": {
            "example_field2": "Invalid value",
            "rfd_status": True,
            "document_on_organisation": {"example_field3": "Invalid value",},
        },
    }
    errors = {
        "pv_grading_details": {"example_field1": ["Example error 1"]},
        "firearm_details": {
            "example_field2": ["Example error 2"],
            "is_covered_by_firearm_act_section_one_two_or_five": ["Error message"],
            "document_on_organisation": {"example_field3": ["Example error 3"],},
        },
    }
    expected = {
        "example_field1": ["Example error 1"],
        "example_field2": ["Example error 2"],
        "example_field3": ["Example error 3"],
        "is_covered_by_firearm_act_section_one_two_or_five": [
            "Select yes if the product is covered by section 5 of the Firearms Act 1968"
        ],
    }
    assert flatten_errors(errors, data) == expected


class DummyDocumentOnOrganisationSerializer(serializers.Serializer):
    document_field = serializers.CharField()


class DummyPVGradingDetailsSerializer(serializers.Serializer):
    pv_grading_field = serializers.CharField()


class DummyFirearmDetailsSerializer(serializers.Serializer):
    firearms_field = serializers.CharField()
    document_on_organisation = DummyDocumentOnOrganisationSerializer()


class DummyGoodSerializer(serializers.Serializer):
    some_field = serializers.CharField()
    firearm_details = DummyFirearmDetailsSerializer()
    pv_grading_details = DummyPVGradingDetailsSerializer()

    def save(self):
        pass


def test_create_or_update_good_errors():
    data = {"some_field": None, "firearm_details": {"document_on_organisation": {},}, "pv_grading_details": {}}
    serializer = DummyGoodSerializer(data=data)
    expected = {
        "errors": {
            "some_field": ["This field may not be null."],
            "firearms_field": ["This field is required."],
            "pv_grading_field": ["This field is required."],
            "document_field": ["This field is required."],
        }
    }
    response = create_or_update_good(serializer, data, False)
    assert json.loads(response.content.decode("utf-8")) == expected
    assert response.status_code == 400


def test_create_or_update_good_validate_only():
    data = {
        "validate_only": True,
        "some_field": "foo",
        "firearm_details": {"firearms_field": "bar", "document_on_organisation": {"document_field": "dlfkj"},},
        "pv_grading_details": {"pv_grading_field": "baz"},
    }
    serializer = DummyGoodSerializer(data=data)
    expected = {
        "good": {
            "some_field": "foo",
            "firearm_details": {"firearms_field": "bar", "document_on_organisation": {"document_field": "dlfkj"},},
            "pv_grading_details": {"pv_grading_field": "baz"},
        }
    }
    response = create_or_update_good(serializer, data, False)
    assert json.loads(response.content.decode("utf-8")) == expected
    assert response.status_code == 200


def test_create_or_update_good_success():
    data = {
        "some_field": "foo",
        "firearm_details": {"firearms_field": "bar", "document_on_organisation": {"document_field": "dlfkj"},},
        "pv_grading_details": {"pv_grading_field": "baz"},
    }
    serializer = DummyGoodSerializer(data=data)
    expected = {
        "good": {
            "some_field": "foo",
            "firearm_details": {"firearms_field": "bar", "document_on_organisation": {"document_field": "dlfkj"},},
            "pv_grading_details": {"pv_grading_field": "baz"},
        }
    }
    response = create_or_update_good(serializer, data, True)
    assert json.loads(response.content.decode("utf-8")) == expected
    assert response.status_code == 201
