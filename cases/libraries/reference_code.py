SLASH = "/"


def generate_reference_code(case):
    # P/GBOIE/2020/000012
    # For licence application cases:
    # First character T or P (temporary or permanent)
    # Second-fourth characters /GB
    # Fifth character O or S (open or standard)
    # Sixth character G or I (general or individual)
    # Seventh character E, T, C (export, transhipment, trade control)
    # For all other case types, prefixes as described below followed by the 4 digit year and 6 digit sequential number:
    # For clearance application cases:
    # F680
    # EXHC - exhibition clearance
    # For query cases
    # EUA for End user advisory
    # GQY for goods queries
    # CRE for HMRC / Border Force customs enquiry/snag
    # For compliance site cases:
    # COMP
    # For compliance visit cases:
    # CVIS
    from cases.enums import CaseTypeEnum
    from applications.libraries.get_applications import get_application
    reference_code = ""

    if case.type == CaseTypeEnum.APPLICATION:
        application = get_application(case.id)

        if hasattr(application, "export_type"):
            reference_code += application.export_type[0] + SLASH

    print('\n')
    print(reference_code)
    print('\n')

    return reference_code.upper()
