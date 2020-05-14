from xml.dom import minidom  # nosec
from xml.etree import ElementTree  # nosec
from xml.sax.saxutils import escape  # nosec

from applications.models import PartyOnApplication, SiteOnApplication
from conf.exceptions import BadRequestError
from lite_content.lite_api.strings import Cases
from parties.enums import PartyRole, PartyType


def dict_to_xml(parent, data):
    for key, value in data.items():
        element = ElementTree.SubElement(parent, key)
        if value:
            element.text = escape(str(value))


def get_party_sh_type(party_on_application):
    if party_on_application["party__role"] == PartyRole.CONTACT:
        return "CONTACT"
    elif party_on_application["party__type"] == PartyType.THIRD_PARTY:
        return "OTHER"
    else:
        return party_on_application["party__type"].upper()


def export_party_on_application_xml(base, party_on_application):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    dict_to_xml(
        stakeholder,
        {
            "ELA_ID": party_on_application["application_id"].int,
            "ELA_DETAIL_ID": None,
            "SH_ID": party_on_application["party_id"].int,
            "SH_TYPE": get_party_sh_type(party_on_application),
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


def export_site_on_application_xml(base, site_on_application):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    dict_to_xml(
        stakeholder,
        {
            "ELA_ID": site_on_application["application_id"].int,
            "ELA_DETAIL_ID": None,
            "SH_ID": site_on_application["site_id"].int,
            "SH_TYPE": "SOURCE",
            "COUNTRY": site_on_application["site__address__country__name"],
            "ORG_NAME": site_on_application["site__organisation__name"],
            "PD_SURNAME": None,
            "PD_FORENAME": None,
            "PD_MIDDLE_INITIALS": None,
            "ADDRESS1": site_on_application["site__address__address_line_1"] or site_on_application["site__address__address"],
            "ADDRESS2": site_on_application["site__address__address_line_2"],
        },
    )
    return stakeholder


def export_cases_xml(case_ids):
    parties_on_applications = (
        PartyOnApplication.objects.filter(application_id__in=case_ids)
        .prefetch_related("party")
        .values(
            "application_id",
            "party_id",
            "party__name",
            "party__type",
            "party__country__name",
            "party__organisation__name",
            "party__address",
            "party__role",
        )
    )

    sites_on_application = (
        SiteOnApplication.objects.filter(application_id__in=case_ids)
        .prefetch_related("site", "site__address")
        .values(
            "application_id",
            "site_id",
            "site__organisation__name",
            "site__address__address",
            "site__address__address_line_1",
            "site__address__address_line_2",
            "site__address__country__name"
        )
    )

    if not parties_on_applications and not sites_on_application:
        raise BadRequestError(Cases.EnforcementCheck.NO_ENTITIES)

    # Build XML structure
    base = ElementTree.Element("ENFORCEMENT_CHECK")
    for poa in parties_on_applications:
        export_party_on_application_xml(base, poa)
    for soa in sites_on_application:
        export_site_on_application_xml(base, soa)

    # Export XML
    xml = ElementTree.tostring(base, encoding="utf-8", method="xml")  # nosec
    reparsed = minidom.parseString(xml)  # nosec
    return reparsed.toprettyxml()
