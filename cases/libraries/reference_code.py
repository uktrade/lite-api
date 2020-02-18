from datetime import datetime

from cases.enums import CaseTypeEnum

SEPARATOR = "/"

# Applications
APPLICATION_PREFIX = "GB"

STANDARD = "S"
OPEN = "O"

INDIVIDUAL = "I"

EXPORT = "E"
TRADE_CONTROL = "C"

LICENCE = "L"

PERMANENT = "P"
TEMPORARY = "T"

# Queries
GOODS_QUERY_PREFIX = "GQY"
END_USER_ADVISORY_QUERY_PREFIX = "EUA"
HMRC_PREFIX = "CRE"

# MOD Clearances
EXHIBITION_CLEARANCE_PREFIX = "EXHC"
F680_CLEARANCE_PREFIX = "F680"
GIFTING_CLEARANCE_PREFIX = "GIFT"


def generate_reference_code(case):
    """
    Generates a unique reference code for each case.

    Example for licence application cases: GBOIE/2020/0000012/P
    First-third characters GB/
    Fourth character O or S (open or standard)
    Fifth character G or I (general or individual)
    Sixth character E, T, C (export, transhipment, trade control)
    Seventh character T or P (temporary or permanent)

    For all other case types, prefixes as described below followed by the 4 digit year and 6 digit sequential number:

    For clearance application cases: F680
    Exhibition clearance: EXHC

    End user advisory: EUA
    Goods queries: GQY
    HMRC / Border Force customs enquiry: CRE
    For compliance site cases: COMP
    For compliance visit cases: CVIS
    """
    from cases.enums import CaseTypeTypeEnum

    reference_code = ""

    if case.case_type.id == CaseTypeEnum.GOODS.id:
        reference_code += GOODS_QUERY_PREFIX + SEPARATOR
    elif case.case_type.id == CaseTypeEnum.EUA.id:
        reference_code += END_USER_ADVISORY_QUERY_PREFIX + SEPARATOR
    elif case.case_type.id == CaseTypeEnum.HMRC.id:
        reference_code += HMRC_PREFIX + SEPARATOR
    elif case.case_type.id == CaseTypeEnum.EXHIBITION.id:
        reference_code += EXHIBITION_CLEARANCE_PREFIX + SEPARATOR
    elif case.case_type.id == CaseTypeEnum.F680.id:
        reference_code += F680_CLEARANCE_PREFIX + SEPARATOR
    elif case.case_type.id == CaseTypeEnum.GIFTING.id:
        reference_code += GIFTING_CLEARANCE_PREFIX + SEPARATOR
    elif case.case_type.type == CaseTypeTypeEnum.APPLICATION:
        # GB
        reference_code += APPLICATION_PREFIX

        # Application type
        reference_code += case.case_type.sub_type[0]

        # General or individual
        reference_code += INDIVIDUAL

        # Export, transhipment and trade control
        if case.application_sites.count():
            reference_code += EXPORT
        elif case.external_application_sites.count():
            reference_code += TRADE_CONTROL

        reference_code += LICENCE + SEPARATOR
    else:
        raise BaseException("Unknown case type")

    # Year
    reference_code += str(datetime.now().year) + SEPARATOR

    # Int
    from cases.models import CaseReferenceCode

    value = CaseReferenceCode.objects.create()
    reference_code += str(value.reference_number).zfill(7)

    if case.case_type.type == CaseTypeTypeEnum.APPLICATION:
        # Export type
        if hasattr(case, "export_type"):
            reference_code += SEPARATOR + case.export_type[0]

    return reference_code.upper()
