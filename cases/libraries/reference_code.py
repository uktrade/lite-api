from datetime import datetime

from applications.enums import ApplicationExportType
from cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum

LICENCE_APPLICATION_PREFIX = "GB"
SEPARATOR = "/"
COMPLIANCE_SITE_SUFFIX = "C"


def generate_reference_code(case):
    from cases.models import CaseReferenceCode

    # Case Reference
    reference_code = case.case_type.reference + SEPARATOR

    # Year
    reference_code += str(datetime.now().year) + SEPARATOR

    # Int
    value = CaseReferenceCode.objects.create()
    reference_code += str(value.reference_number).zfill(7)

    # Licence Applications
    if case.case_type.sub_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
        reference_code = LICENCE_APPLICATION_PREFIX + reference_code

        # Export type
        if case.export_type in [ApplicationExportType.TEMPORARY, ApplicationExportType.PERMANENT]:
            reference_code += SEPARATOR + case.export_type[0]

    if case.case_type.id == CaseTypeEnum.COMPLIANCE.id:
        reference_code += SEPARATOR + COMPLIANCE_SITE_SUFFIX

    return reference_code.upper()
