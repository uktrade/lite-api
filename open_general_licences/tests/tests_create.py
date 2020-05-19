from rest_framework.reverse import reverse

from cases.enums import CaseTypeEnum

URL = reverse("open_general_licences:list")

REQUEST_DATA = {
    "name": "Open general export licence (low value shipments)",
    "description": "Licence allowing the export of low value shipments of certain goods.",
    "url": "https://www.gov.uk/government/publications/open-general-export-licence-low-value-shipments",
    "case_type": CaseTypeEnum.OGEL,
    "countries": ["CA"],
    "control_list_entries": ["ML1a"],
}

def tests