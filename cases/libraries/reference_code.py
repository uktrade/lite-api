import asyncio
from datetime import datetime

from applications.enums import ApplicationExportType
from cases.enums import CaseTypeSubTypeEnum

LICENCE_APPLICATION_PREFIX = "GB"
SEPARATOR = "/"


@asyncio.coroutine
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

    return reference_code.upper()
