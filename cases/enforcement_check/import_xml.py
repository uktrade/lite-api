from xml.etree.ElementTree import ParseError  # nosec

from defusedxml import ElementTree
from django.db import transaction
from rest_framework.exceptions import ValidationError
import os
import xmlschema

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from cases.enums import EnforcementXMLEntityTypes
from cases.models import EnforcementCheckID, Case
from api.conf.settings import BASE_DIR
from api.flags.enums import SystemFlags
from lite_content.lite_api.strings import Cases
from api.users.enums import SystemUser
from api.users.models import BaseUser
from api.workflow.user_queue_assignment import user_queue_assignment_workflow

APPLICATION_ID_TAG = "CODE1"
ENTITY_ID_TAG = "CODE2"
FLAG_TAG = "FLAG"
XML_SCHEMA = xmlschema.XMLSchema(os.path.join(BASE_DIR, "cases", "enforcement_check", "import_format.xsd"))


def import_cases_xml(file, queue):
    """
    Takes an XML string and validates it matches the expected format.
    Removes the "Enforcement check required" flag for any matching cases
    and sets flags for any matching entities found in the XML (i.e. sites, end users etc.)
    """
    try:
        if not XML_SCHEMA.is_valid(file):
            raise ValidationError({"file": [Cases.EnforcementUnit.INVALID_XML_FORMAT]})

        tree = ElementTree.fromstring(file)
        data = [{element.tag: element.text for element in child} for child in tree]

        data = _convert_ids_to_uuids(data)
        _set_flags(data)
        _trigger_workflow(data, queue)
    except ParseError:
        raise ValidationError({"file": [Cases.EnforcementUnit.INVALID_FORMAT]})


def enforcement_id_to_uuid(id):
    return EnforcementCheckID.objects.get(id=id).entity_id


def _convert_ids_to_uuids(data):
    all_ids = set([item[APPLICATION_ID_TAG] for item in data] + [item[ENTITY_ID_TAG] for item in data])
    uuids = EnforcementCheckID.objects.filter(id__in=all_ids).values("id", "entity_id", "entity_type")

    if len(all_ids) != len(uuids):
        ids_not_found = all_ids.difference(set([str(id) for id in uuids.values_list("id", flat=True)]))
        raise ValidationError({"file": [Cases.EnforcementUnit.INVALID_ID_FORMAT + ", ".join(ids_not_found)]})

    uuids = {str(item["id"]): item for item in uuids}
    return [
        {
            "application": uuids[item[APPLICATION_ID_TAG]]["entity_id"],
            "entity": uuids[item[ENTITY_ID_TAG]]["entity_id"],
            "type": uuids[item[ENTITY_ID_TAG]]["entity_type"],
            "match": item[FLAG_TAG] == "Y",
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


def _trigger_workflow(data, queue):
    system_user = BaseUser.objects.get(id=SystemUser.id)
    applications = set([item["application"] for item in data])
    applications_without_matches = []

    for application in applications:
        if not any([item["match"] for item in data if item["application"] == application]):
            applications_without_matches.append(application)

    cases_to_apply_workflow = Case.objects.filter(id__in=applications_without_matches)
    for case in cases_to_apply_workflow:
        user_queue_assignment_workflow([queue], case)
        audit_trail_service.create(
            actor=system_user, verb=AuditType.UNASSIGNED, target=case,
        )


def _add_flag_if_not_exists(flag, case_id):
    if not Case.objects.filter(id=case_id, flags__id=flag).exists():
        Case.objects.get(id=case_id).flags.add(flag)


def _remove_enforcement_flags(ids):
    for id in ids:
        if Case.objects.filter(id=id, flags__id=SystemFlags.ENFORCEMENT_CHECK_REQUIRED).exists():
            Case.objects.get(id=id).flags.remove(SystemFlags.ENFORCEMENT_CHECK_REQUIRED)
