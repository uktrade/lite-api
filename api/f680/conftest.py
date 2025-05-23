from copy import deepcopy

import pytest

from api.f680.tests.f680_test_data import (
    AUSTRALIA_RELEASE_ID,
    FRANCE_RELEASE_ID,
    UAE_RELEASE_ID,
    APPLICATION_JSON,
)


@pytest.fixture
def data_australia_release_id():
    return AUSTRALIA_RELEASE_ID


@pytest.fixture
def data_france_release_id():
    return FRANCE_RELEASE_ID


@pytest.fixture
def data_uae_release_id():
    return UAE_RELEASE_ID


@pytest.fixture
def data_application_json():
    return deepcopy(APPLICATION_JSON)


@pytest.fixture
def data_application_json_no_security_prefix(data_application_json):
    data_application_json["sections"]["product_information"] = {
        "label": "Product information",
        "fields": {
            "product_name": {
                "key": "product_name",
                "answer": "dfg",
                "raw_answer": "dfg",
                "question": "Give the item a descriptive name",
                "datatype": "string",
            },
            "product_description": {
                "key": "product_description",
                "answer": "dfg",
                "raw_answer": "dfg",
                "question": "Describe the item",
                "datatype": "string",
            },
            "has_security_classification": {
                "key": "has_security_classification",
                "answer": "No",
                "raw_answer": False,
                "question": "Has the product been given a security classification by a UK MOD authority?",
                "datatype": "boolean",
            },
            "actions_to_classify": {
                "key": "actions_to_classify",
                "answer": "dfg",
                "raw_answer": "dfg",
                "question": "Provide details on what action will have to be taken to have the product security classified",
                "datatype": "string",
            },
            "is_foreign_tech_or_information_shared": {
                "key": "is_foreign_tech_or_information_shared",
                "answer": "No",
                "raw_answer": False,
                "question": "Will any foreign technology or information be shared with the item?",
                "datatype": "boolean",
            },
            "is_including_cryptography_or_security_features": {
                "key": "is_including_cryptography_or_security_features",
                "answer": "No",
                "raw_answer": False,
                "question": "Does the item include cryptography or other information security features?",
                "datatype": "boolean",
            },
            "cryptography_or_security_feature_info": {
                "key": "cryptography_or_security_feature_info",
                "answer": "",
                "raw_answer": "",
                "question": "Provide full details",
                "datatype": "string",
            },
            "is_item_rated_under_mctr": {
                "key": "is_item_rated_under_mctr",
                "answer": "No",
                "raw_answer": "no",
                "question": "Do you believe the item is rated under the Missile Technology Control Regime (MTCR)",
                "datatype": "string",
            },
            "is_item_manpad": {
                "key": "is_item_manpad",
                "answer": "No, the product is not a MANPADS",
                "raw_answer": "no",
                "question": "Do you believe the item is a man-portable air defence system (MANPADS)?",
                "datatype": "string",
            },
            "is_mod_electronic_data_shared": {
                "key": "is_mod_electronic_data_shared",
                "answer": "No",
                "raw_answer": "no",
                "question": "Will any electronic warfare data owned by the Ministry of Defence (MOD) be shared with the item?",
                "datatype": "string",
            },
            "funding_source": {
                "key": "funding_source",
                "answer": "Private venture",
                "raw_answer": "private_venture",
                "question": "Who is funding the item?",
                "datatype": "string",
            },
            "is_used_by_uk_armed_forces": {
                "key": "is_used_by_uk_armed_forces",
                "answer": "No",
                "raw_answer": False,
                "question": "Will the item be used by the UK Armed Forces?",
                "datatype": "boolean",
            },
            "used_by_uk_armed_forces_info": {
                "key": "used_by_uk_armed_forces_info",
                "answer": "",
                "raw_answer": "",
                "question": "Explain how it will be used",
                "datatype": "string",
            },
        },
        "fields_sequence": [
            "product_name",
            "product_description",
            "has_security_classification",
            "actions_to_classify",
            "is_foreign_tech_or_information_shared",
            "is_including_cryptography_or_security_features",
            "cryptography_or_security_feature_info",
            "is_item_rated_under_mctr",
            "is_item_manpad",
            "is_mod_electronic_data_shared",
            "funding_source",
            "is_used_by_uk_armed_forces",
            "used_by_uk_armed_forces_info",
        ],
        "type": "single",
    }
    return data_application_json
