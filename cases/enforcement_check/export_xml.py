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


def get_parties_on_applications(case_ids):
    return (
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
            "ADDRESS1": site_on_application["site__address__address_line_1"]
            or site_on_application["site__address__address"],
            "ADDRESS2": site_on_application["site__address__address_line_2"],
        },
    )
    return stakeholder


def get_sites_on_applications(case_ids):
    return (
        SiteOnApplication.objects.filter(application_id__in=case_ids)
        .prefetch_related("site", "site__address")
        .values(
            "application_id",
            "site_id",
            "site__organisation__name",
            "site__address__address",
            "site__address__address_line_1",
            "site__address__address_line_2",
            "site__address__country__name",
        )
    )


def export_organisation_on_application_xml(base, organisation_on_application):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    dict_to_xml(
        stakeholder,
        {
            "ELA_ID": organisation_on_application["id"].int,
            "ELA_DETAIL_ID": None,
            "SH_ID": organisation_on_application["organisation_id"].int,
            "SH_TYPE": "LICENSEE",
            "COUNTRY": organisation_on_application["organisation__primary_site__address__country__name"],
            "ORG_NAME": organisation_on_application["organisation__name"],
            "PD_SURNAME": None,
            "PD_FORENAME": None,
            "PD_MIDDLE_INITIALS": None,
            "ADDRESS1": organisation_on_application["organisation__primary_site__address__address_line_1"]
            or organisation_on_application["organisation__primary_site__address__address"],
            "ADDRESS2": organisation_on_application["organisation__primary_site__address__address_line_2"],
        },
    )
    return stakeholder


def get_organisations_on_applications(cases):
    return cases.prefetch_related("organisation", "organisation__primary_site").values(
        "id",
        "organisation_id",
        "organisation__name",
        "organisation__primary_site__address__address",
        "organisation__primary_site__address__address_line_1",
        "organisation__primary_site__address__address_line_2",
        "organisation__primary_site__address__country__name",
    )


def export_cases_xml(cases):
    case_ids = cases.values_list("pk", flat=True)
    parties_on_applications = get_parties_on_applications(case_ids)
    sites_on_applications = get_sites_on_applications(case_ids)
    organisations_on_applications = get_organisations_on_applications(cases)

    # Build XML structure
    base = ElementTree.Element("ENFORCEMENT_CHECK")
    for poa in parties_on_applications:
        export_party_on_application_xml(base, poa)
    for soa in sites_on_applications:
        export_site_on_application_xml(base, soa)
    for org in organisations_on_applications:
        export_organisation_on_application_xml(base, org)

    # Export XML
    xml = ElementTree.tostring(base, encoding="utf-8", method="xml")  # nosec
    reparsed = minidom.parseString(xml)  # nosec
    return reparsed.toprettyxml()
