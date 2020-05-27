from defusedxml import ElementTree
from defusedxml.ElementTree import ParseError
from rest_framework.exceptions import ValidationError

from cases.models import EnforcementCheckID


def import_cases_xml(file):
    try:
        tree = ElementTree.fromstring(file)
        data = _extract_and_validate_xml_tree(tree)
        _validate_entity_ids(data)
    except ParseError as e:
        raise ValidationError({"file": ["Invalid format received"]})


def enforcement_id_to_uuid(id):
    return EnforcementCheckID.objects.get(id=id).entity_id


def _extract_and_validate_xml_tree(tree):
    data = []
    try:
        assert tree.tag == 'SPIRE_UPLOAD'
        for child in tree:
            assert child.tag == 'SPIRE_RETURNS'
            elements = {element.tag: element.text for element in child}
            assert {'FLAG', 'CODE2', 'CODE1'}.issubset(elements.keys())
            assert all(elements.values())
            data.append(elements)
    except AssertionError as e:
        raise ValidationError({"file": ["Invalid XML format received"]})

    return data


def _validate_entity_ids(data):
    ids = EnforcementCheckID.objects.values_list("id", flat=True)
    try:
        assert {item["CODE1"] for item in data}.issubset(ids)
        assert {item["CODE2"] for item in data}.issubset(ids)
    except AssertionError as e:
        raise ValidationError({"file": ["Invalid entity ID received"]})
