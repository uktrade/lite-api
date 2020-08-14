from datetime import datetime
from django.utils import timezone

from api.applications.enums import ApplicationExportType
from cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum

LICENCE_APPLICATION_PREFIX = "GB"
SEPARATOR = "/"


def generate_reference_code(case):
    from cases.models import CaseReferenceCode

    # Case Reference
    if case.case_type.id in [CaseTypeEnum.COMPLIANCE_SITE.id, CaseTypeEnum.COMPLIANCE_VISIT.id]:
        compliance_prefix, compliance_suffix = case.case_type.reference.split("_")
        reference_code = compliance_prefix + SEPARATOR
    else:
        reference_code = case.case_type.reference + SEPARATOR

    # Year
    reference_code += str(timezone.make_aware(datetime.now()).year) + SEPARATOR

    # Int
    value = CaseReferenceCode.objects.create()
    reference_code += str(value.reference_number).zfill(7)

    # Licence Applications
    if case.case_type.sub_type in [CaseTypeSubTypeEnum.STANDARD, CaseTypeSubTypeEnum.OPEN]:
        reference_code = LICENCE_APPLICATION_PREFIX + reference_code

        # Export type
        if hasattr(case, "export_type"):
            if case.export_type in [ApplicationExportType.TEMPORARY, ApplicationExportType.PERMANENT]:
                reference_code += SEPARATOR + case.export_type[0]

    if case.case_type.id in [CaseTypeEnum.COMPLIANCE_SITE.id, CaseTypeEnum.COMPLIANCE_VISIT.id]:
        reference_code += SEPARATOR + compliance_suffix

    return reference_code.upper()
