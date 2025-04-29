from api.applications.enums import ApplicationExportType
from api.cases.enums import (
    CaseTypeEnum,
    CaseTypeTypeEnum,
)

LICENCE_APPLICATION_PREFIX = "GB"
SEPARATOR = "/"


def generate_reference_code(case):
    from api.cases.models import CaseReferenceCode

    parts = []

    case_type = CaseTypeEnum.reference_to_class(case.case_type.reference)
    reference_code_identifier = getattr(case_type, "reference_code_identifier", case_type.reference)
    if case.case_type.type == CaseTypeTypeEnum.APPLICATION:
        reference_code_identifier = f"{LICENCE_APPLICATION_PREFIX}{reference_code_identifier}"
    parts.append(reference_code_identifier)

    case_reference_code = CaseReferenceCode.objects.create()
    parts.append(str(case_reference_code.year))
    parts.append(str(case_reference_code.reference_number).zfill(7))

    # Licence Applications
    if (
        case.case_type.type == CaseTypeTypeEnum.APPLICATION
        and hasattr(case, "export_type")
        and case.export_type in [ApplicationExportType.TEMPORARY, ApplicationExportType.PERMANENT]
    ):
        parts.append(case.export_type[0])

    return SEPARATOR.join(parts).upper()
