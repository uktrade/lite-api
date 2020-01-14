from datetime import datetime

SLASH = "/"


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
    from cases.models import Case
    from cases.enums import CaseTypeEnum

    reference_code = ""

    if case.type == CaseTypeEnum.APPLICATION:
        # Export type
        if hasattr(case, "export_type"):
            reference_code += case.export_type[0] + SLASH

        # GB
        reference_code += "GB"

        # Application type
        if hasattr(case, "application_type"):
            reference_code += case.application_type[0]

        # General or individual
        reference_code += "?"

        # Export, transhipment and trade control
        reference_code += "?" + SLASH

    if case.type == CaseTypeEnum.CLC_QUERY:
        reference_code += "GQY" + SLASH

    if case.type == CaseTypeEnum.END_USER_ADVISORY_QUERY:
        reference_code += "EUA" + SLASH

    if case.type == CaseTypeEnum.HMRC_QUERY:
        reference_code += "CRE" + SLASH

    # Year
    reference_code += str(datetime.now().year) + SLASH

    # Int
    from cases.models import CaseReferenceCode

    value = CaseReferenceCode.objects.create()
    reference_code += str(value.reference_number).zfill(7)

    return reference_code.upper()
