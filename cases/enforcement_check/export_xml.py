from xml.dom import minidom  # nosec
from xml.etree import ElementTree  # nosec
from xml.sax.saxutils import escape  # nosec

from api.applications.models import PartyOnApplication, SiteOnApplication, ExternalLocationOnApplication
from cases.enums import EnforcementXMLEntityTypes
from cases.models import EnforcementCheckID
from api.parties.enums import PartyRole, PartyType


def export_cases_xml(cases):
    """
    Takes a list of cases and converts into XML for the enforcement unit.
    XML includes party details, sites & the organisation for each application.
    """
    case_ids = cases.values_list("pk", flat=True)

    # Build XML structure
    base = ElementTree.Element("ENFORCEMENT_CHECK")
    _export_parties_on_application(case_ids, base)
    _export_sites_on_applications(case_ids, base)
    _export_external_locations_on_applications(case_ids, base)
    _export_organisations_on_applications(cases, base)

    # Export XML
    xml = ElementTree.tostring(base, encoding="utf-8", method="xml")  # nosec
    reparsed = minidom.parseString(xml).toprettyxml()  # nosec
    return reparsed


def get_enforcement_id(uuid):
    return EnforcementCheckID.objects.get(entity_id=uuid).id


def _uuid_to_enforcement_id(uuid, type):
    enforcement_check_id, _ = EnforcementCheckID.objects.get_or_create(entity_id=uuid, entity_type=type)
    return enforcement_check_id.id


def _dict_to_xml(parent, data):
    for key, value in data.items():
        element = ElementTree.SubElement(parent, key)
        if value:
            element.text = escape(str(value))


def _get_address_line_2(address_line_2, postcode, city):
    if address_line_2:
        return ", ".join([address_line_2, postcode, city])
    elif postcode and city:
        return ", ".join([postcode, city])


def _format_address(address):
    if address:
        return address.replace("\n", " ")


def _entity_to_xml(
    base, application_id, id, type, sh_type, country, organisation, address_line_1, name=None, address_line_2=None
):
    stakeholder = ElementTree.SubElement(base, "STAKEHOLDER")
    _dict_to_xml(
        stakeholder,
        {
            "ELA_ID": _uuid_to_enforcement_id(application_id, EnforcementXMLEntityTypes.APPLICATION),
            "ELA_DETAIL_ID": _uuid_to_enforcement_id(id, type),
            "SH_ID": _uuid_to_enforcement_id(id, type),
            "SH_TYPE": sh_type,
            "COUNTRY": country,
            "ORG_NAME": organisation,
            "PD_SURNAME": name,
            "PD_FORENAME": None,
            "PD_MIDDLE_INITIALS": None,
            "ADDRESS1": _format_address(address_line_1),
            "ADDRESS2": _format_address(address_line_2),
        },
    )
    return stakeholder


def _get_party_sh_type(type, role):
    if role == PartyRole.CONTACT:
        return "CONTACT"
    elif type == PartyType.THIRD_PARTY:
        return "OTHER"
    else:
        return type.upper()


def _export_parties_on_application(case_ids, xml_base):
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
        _entity_to_xml(
            xml_base,
            application_id=poa["application_id"],
            id=poa["party_id"],
            type=poa["party__type"],
            sh_type=_get_party_sh_type(type=poa["party__type"], role=poa["party__role"]),
            country=poa["party__country__name"],
            organisation=poa["party__organisation__name"],
            name=poa["party__name"],
            address_line_1=poa["party__address"],
        )


def _export_external_locations_on_applications(case_ids, xml_base):
    external_locations = (
        ExternalLocationOnApplication.objects.filter(application_id__in=case_ids)
        .prefetch_related("external_location")
        .values(
            "application_id",
            "external_location_id",
            "external_location__country__name",
            "external_location__organisation__name",
            "external_location__address",
        )
    )
    for location in external_locations:
        _entity_to_xml(
            xml_base,
            application_id=location["application_id"],
            id=location["external_location_id"],
            type=EnforcementXMLEntityTypes.SITE,
            sh_type="SOURCE",
            country=location["external_location__country__name"],
            organisation=location["external_location__organisation__name"],
            address_line_1=location["external_location__address"],
        )


def _export_sites_on_applications(case_ids, xml_base):
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
            "site__address__postcode",
            "site__address__city",
        )
    )
    for soa in sites_on_applications:
        _entity_to_xml(
            xml_base,
            application_id=soa["application_id"],
            id=soa["site_id"],
            type=EnforcementXMLEntityTypes.SITE,
            sh_type="SOURCE",
            country=soa["site__address__country__name"],
            organisation=soa["site__organisation__name"],
            address_line_1=soa["site__address__address_line_1"] or soa["site__address__address"],
            address_line_2=_get_address_line_2(
                soa["site__address__address_line_2"], soa["site__address__postcode"], soa["site__address__city"]
            ),
        )


def _export_organisations_on_applications(cases, xml_base):
    organisations_on_applications = cases.prefetch_related(
        "organisation", "organisation__primary_site__address"
    ).values(
        "id",
        "organisation_id",
        "organisation__name",
        "organisation__primary_site__address__address",
        "organisation__primary_site__address__address_line_1",
        "organisation__primary_site__address__address_line_2",
        "organisation__primary_site__address__country__name",
        "organisation__primary_site__address__postcode",
        "organisation__primary_site__address__city",
    )
    for org in organisations_on_applications:
        _entity_to_xml(
            xml_base,
            application_id=org["id"],
            id=org["organisation_id"],
            type=EnforcementXMLEntityTypes.ORGANISATION,
            sh_type="LICENSEE",
            country=org["organisation__primary_site__address__country__name"],
            organisation=org["organisation__name"],
            address_line_1=org["organisation__primary_site__address__address_line_1"]
            or org["organisation__primary_site__address__address"],
            address_line_2=_get_address_line_2(
                org["organisation__primary_site__address__address_line_2"],
                org["organisation__primary_site__address__postcode"],
                org["organisation__primary_site__address__city"],
            ),
        )
