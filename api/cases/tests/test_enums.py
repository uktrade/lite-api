import pytest
import uuid

from api.cases.enums import (
    CaseTypeEnum,
    CaseTypeSubTypeEnum,
    CaseTypeTypeEnum,
)
from api.cases.tests.factories import CaseTypeFactory


pytestmark = pytest.mark.django_db


def test_case_type_type_enum_get_case_type():
    case_type = CaseTypeFactory(type="test_case_type")
    assert CaseTypeTypeEnum.get_case_type(case_type) == "test_case_type"


def test_case_type_sub_type_enum_get_case_type():
    case_type = CaseTypeFactory(sub_type="test_case_sub_type")
    assert CaseTypeSubTypeEnum.get_case_type(case_type) == "test_case_sub_type"


def test_case_type_case_type_enum_get_case_type():
    pk = uuid.uuid4()
    case_type = CaseTypeFactory(id=pk)
    assert CaseTypeEnum.get_case_type(case_type) == pk
