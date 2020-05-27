from defusedxml import ElementTree
from defusedxml.ElementTree import ParseError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from cases.enums import EnforcementXMLEntityTypes
from cases.models import EnforcementCheckID, Case
from flags.enums import SystemFlags


def import_cases_xml(file):
    try:
        tree = ElementTree.fromstring(file)
        data = _extract_and_validate_xml_tree(tree)
        data = _convert_ids_to_uuids(data)
        _set_flags(data)
    except ParseError as e:
        raise ValidationError({"file": ["Invalid format received"]})


def enforcement_id_to_uuid(id):
    return EnforcementCheckID.objects.get(id=id).entity_id


def _extract_and_validate_xml_tree(tree):
    data = []
    try:
        assert tree.tag == "SPIRE_UPLOAD"
        for child in tree:
            assert child.tag == "SPIRE_RETURNS"
            elements = {element.tag: element.text for element in child}
            assert {"FLAG", "CODE2", "CODE1"}.issubset(elements.keys())
            assert all(elements.values())
            assert elements["FLAG"] == "Y" or elements["FLAG"] == "N"
            assert int(elements["CODE1"])
            assert int(elements["CODE2"])
            data.append(elements)
    except AssertionError as e:
        raise ValidationError({"file": ["Invalid XML format received"]})
    except ValueError as e:
        raise ValidationError({"file": ["Invalid ID received"]})

    return data


def _convert_ids_to_uuids(data):
    all_ids = set([item["CODE1"] for item in data] + [item["CODE2"] for item in data])
    uuids = EnforcementCheckID.objects.filter(id__in=all_ids).values("id", "entity_id", "entity_type")

    if len(all_ids) != len(uuids):
        raise ValidationError({"file": ["Invalid entity ID received"]})

    uuids = {str(item["id"]): item for item in uuids}
    return [
        {
            "application": uuids[item["CODE1"]]["entity_id"],
            "entity": uuids[item["CODE2"]]["entity_id"],
            "type": uuids[item["CODE2"]]["entity_type"],
            "match": item["FLAG"] == "Y",
        }
        for item in data
    ]


def _set_flags(data):
    with transaction.atomic():
        _remove_enforcement_flags([item["application"] for item in data])
        for item in data:
            if item["match"]:
                if item["type"] == EnforcementXMLEntityTypes.ORGANISATION:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_ORGANISATION_MATCH, item["application"])
                elif item["type"] == EnforcementXMLEntityTypes.SITE:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_SITE_MATCH, item["application"])
                elif item["type"] == EnforcementXMLEntityTypes.END_USER:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_END_USER_MATCH, item["application"])
                elif item["type"] == EnforcementXMLEntityTypes.CONSIGNEE:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_CONSIGNEE_MATCH, item["application"])
                elif item["type"] == EnforcementXMLEntityTypes.ULTIMATE_END_USER:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_ULTIMATE_END_USER_MATCH, item["application"])
                elif item["type"] == EnforcementXMLEntityTypes.THIRD_PARTY:
                    _add_flag_if_not_exists(SystemFlags.ENFORCEMENT_THIRD_PARTY_MATCH, item["application"])


def _add_flag_if_not_exists(flag, case_id):
    if not Case.objects.filter(id=case_id, flags__id=flag).exists():
        Case.objects.get(id=case_id).flags.add(flag)


def _remove_enforcement_flags(ids):
    for id in ids:
        if Case.objects.filter(id=id, flags__id=SystemFlags.ENFORCEMENT_CHECK_REQUIRED).exists():
            Case.objects.get(id=id).flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
