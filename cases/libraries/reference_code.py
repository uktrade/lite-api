from datetime import datetime

SEPARATOR = "/"

# Applications
APPLICATION_PREFIX = "GB"

STANDARD = "S"
OPEN = "O"

INDIVIDUAL = "I"

EXPORT = "E"
TRADE_CONTROL = "C"

PERMANENT = "P"
TEMPORARY = "T"

# Queries
GOODS_QUERY_PREFIX = "GQY"
END_USER_ADVISORY_QUERY_PREFIX = "EUA"
HMRC_QUERY_PREFIX = "CRE"

# MOD Clearances
EXHIBITION_CLEARANCE_PREFIX = "EXHC"
F680_CLEARANCE_PREFIX = "F680"
GIFTING_CLEARANCE_PREFIX = "GIFT"


def generate_reference_code(case):
    """
    Generates a unique reference code for each case.

    Example for licence application cases: P/GBOIE/2020/0000012
    First character T or P (temporary or permanent)
    Second-fourth characters /GB
    Fifth character O or S (open or standard)
    Sixth character G or I (general or individual)
    Seventh character E, T, C (export, transhipment, trade control)

    For all other case types, prefixes as described below followed by the 4 digit year and 6 digit sequential number:

    For clearance application cases: F680
    Exhibition clearance: EXHC

    End user advisory: EUA
    Goods queries: GQY
    HMRC / Border Force customs enquiry: CRE
    For compliance site cases: COMP
    For compliance visit cases: CVIS
    """
    from cases.enums import CaseTypeEnum

    reference_code = ""

    if case.type == CaseTypeEnum.APPLICATION:
        # GB
        reference_code += APPLICATION_PREFIX

        # Application type
        if hasattr(case, "application_type"):
            reference_code += case.application_type[0]

        # General or individual
        reference_code += INDIVIDUAL

        # Export, transhipment and trade control
        if case.application_sites.count():
            reference_code += EXPORT + SEPARATOR
        elif case.external_application_sites.count():
            reference_code += TRADE_CONTROL + SEPARATOR
    elif case.type == CaseTypeEnum.GOODS_QUERY:
        reference_code += GOODS_QUERY_PREFIX + SEPARATOR
    elif case.type == CaseTypeEnum.END_USER_ADVISORY_QUERY:
        reference_code += END_USER_ADVISORY_QUERY_PREFIX + SEPARATOR
    elif case.type == CaseTypeEnum.HMRC_QUERY:
        reference_code += HMRC_QUERY_PREFIX + SEPARATOR
    elif case.type == CaseTypeEnum.EXHIBITION_CLEARANCE:
        reference_code += EXHIBITION_CLEARANCE_PREFIX + SEPARATOR
    elif case.type == CaseTypeEnum.F680_CLEARANCE:
        reference_code += F680_CLEARANCE_PREFIX + SEPARATOR
    elif case.type == CaseTypeEnum.GIFTING_CLEARANCE:
        reference_code += GIFTING_CLEARANCE_PREFIX + SEPARATOR

    # Year
    reference_code += str(datetime.now().year) + SEPARATOR

    # Int
    from cases.models import CaseReferenceCode

    value = CaseReferenceCode.objects.create()
    reference_code += str(value.reference_number).zfill(7)

    if case.type == CaseTypeEnum.APPLICATION:
        # Export type
        if hasattr(case, "export_type"):
            reference_code += SEPARATOR + case.export_type[0]

    return reference_code.upper()
