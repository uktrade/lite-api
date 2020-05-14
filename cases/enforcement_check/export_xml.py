from xml.dom import minidom  # nosec
from xml.etree import ElementTree  # nosec
from xml.sax.saxutils import escape  # nosec

from applications.models import PartyOnApplication, SiteOnApplication
from parties.enums import PartyRole, PartyType


def dict_to_xml(parent, data):
    for key, value in data.items():
        element = ElementTree.SubElement(parent, key)
        if value:
            element.text = escape(str(value))


def entity_to_xml(
    base, application_id, id, type, country, organisation, address_line_1, name=None, address_line_2=None
):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    dict_to_xml(
        stakeholder,
        {
            "ELA_ID": application_id.int,
            "ELA_DETAIL_ID": None,
            "SH_ID": id.int,
            "SH_TYPE": type,
            "COUNTRY": country,
            "ORG_NAME": organisation,
            "PD_SURNAME": name,
            "PD_FORENAME": None,
            "PD_MIDDLE_INITIALS": None,
            "ADDRESS1": address_line_1,
            "ADDRESS2": address_line_2,
        },
    )
    return stakeholder


def get_party_sh_type(type, role):
    if role == PartyRole.CONTACT:
        return "CONTACT"
    elif type == PartyType.THIRD_PARTY:
        return "OTHER"
    else:
        return type.upper()


def export_parties_on_application(case_ids, xml_base):
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
    for poa in parties_on_applications:
        entity_to_xml(
            xml_base,
            application_id=poa["application_id"],
            id=poa["party_id"],
            type=get_party_sh_type(type=poa["party__type"], role=poa["party__role"]),
            country=poa["party__country__name"],
            organisation=poa["party__organisation__name"],
            name=poa["party__name"],
            address_line_1=poa["party__address"],
        )


def export_sites_on_applications(case_ids, xml_base):
    sites_on_applications = (
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
    for soa in sites_on_applications:
        entity_to_xml(
            xml_base,
            application_id=soa["application_id"],
            id=soa["site_id"],
            type="SOURCE",
            country=soa["site__address__country__name"],
            organisation=soa["site__organisation__name"],
            address_line_1=soa["site__address__address_line_1"] or soa["site__address__address"],
            address_line_2=soa["site__address__address_line_2"],
        )


def export_organisations_on_applications(cases, xml_base):
    organisations_on_applications = cases.prefetch_related("organisation", "organisation__primary_site").values(
        "id",
        "organisation_id",
        "organisation__name",
        "organisation__primary_site__address__address",
        "organisation__primary_site__address__address_line_1",
        "organisation__primary_site__address__address_line_2",
        "organisation__primary_site__address__country__name",
    )
    for org in organisations_on_applications:
        entity_to_xml(
            xml_base,
            application_id=org["id"],
            id=org["organisation_id"],
            type="LICENSEE",
            country=org["organisation__primary_site__address__country__name"],
            organisation=org["organisation__name"],
            address_line_1=org["organisation__primary_site__address__address_line_1"]
            or org["organisation__primary_site__address__address"],
            address_line_2=org["organisation__primary_site__address__address_line_2"]
        )


def export_cases_xml(cases):
    case_ids = cases.values_list("pk", flat=True)

    # Build XML structure
    base = ElementTree.Element("ENFORCEMENT_CHECK")
    export_parties_on_application(case_ids, base)
    export_sites_on_applications(case_ids, base)
    export_organisations_on_applications(cases, base)

    # Export XML
    xml = ElementTree.tostring(base, encoding="utf-8", method="xml")  # nosec
    reparsed = minidom.parseString(xml)  # nosec
    return reparsed.toprettyxml()
