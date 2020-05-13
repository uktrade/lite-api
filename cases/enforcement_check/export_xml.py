from xml.dom import minidom  # nosec
from xml.etree import ElementTree  # nosec

from applications.models import PartyOnApplication


def dict_to_xml(parent, data):
    for key, value in data.items():
        element = ElementTree.SubElement(parent, key)
        if value:
            element.text = str(value)


def export_party_on_application_xml(base, party_on_application):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    dict_to_xml(
        stakeholder,
        {
            "ELA_ID": party_on_application["application_id"].int,
            "ELA_DETAIL_ID": None,
            "SH_ID": party_on_application["party_id"].int,
            "SH_TYPE": party_on_application["party__type"].upper(),
            "COUNTRY": party_on_application["party__country__name"],
            "ORG_NAME": party_on_application["party__organisation__name"],
            "PD_SURNAME": party_on_application["party__name"],
            "PD_FORENAME": None,
            "PD_MIDDLE_INITIALS": None,
            "ADDRESS1": party_on_application["party__address"],
            "ADDRESS2": None,
        },
    )
    return stakeholder


def export_cases_xml(application_ids):
    parties_on_applications = (
        PartyOnApplication.objects.filter(application_id__in=application_ids)
        .prefetch_related("party")
        .values(
            "application_id",
            "party_id",
            "party__name",
            "party__type",
            "party__country__name",
            "party__organisation__name",
            "party__address",
        )
    )

    base = ElementTree.Element("ENFORCEMENT_CHECK")
    for poa in parties_on_applications:
        export_party_on_application_xml(base, poa)

    xml = ElementTree.tostring(base, encoding="utf-8", method="xml")  # nosec
    reparsed = minidom.parseString(xml)  # nosec
    return reparsed.toprettyxml()
