from api.cases.enums import CaseTypeReferenceEnum


CASE_TYPE_MAP = {
    CaseTypeReferenceEnum.SIEL: "SIE",
    CaseTypeReferenceEnum.SITL: "SIE",
    CaseTypeReferenceEnum.OIEL: "OIE",
    CaseTypeReferenceEnum.OGEL: "OGE",
    CaseTypeReferenceEnum.OICL: "OIT",
    CaseTypeReferenceEnum.OGTCL: "OGT",
    CaseTypeReferenceEnum.SICL: "SIT",
    CaseTypeReferenceEnum.F680: "MDF",
    CaseTypeReferenceEnum.GIFT: "GFT",
    CaseTypeReferenceEnum.EXHC: "EXC",
    CaseTypeReferenceEnum.EUA: "AEU",
    CaseTypeReferenceEnum.GQY: "ECL",
    CaseTypeReferenceEnum.CRE: "CRE",
    CaseTypeReferenceEnum.COMP_SITE: "CSC",
    CaseTypeReferenceEnum.COMP_VISIT: "CVC",
}


class UnknownApplicationTypeError(ValueError):
    pass


def generate_reference_code(case):
    """
    Function that generates the case/application reference code
    as per the new referencing scheme
    """
    from api.cases.models import CaseReferenceCode

    try:
        case_type = CASE_TYPE_MAP[case.case_type.reference]
    except KeyError as err:
        raise UnknownApplicationTypeError(
            f"Application type {case.case_type.reference} currently not supported"
        ) from err

    ref_code = CaseReferenceCode.objects.create()
    return f"{case_type}{str(ref_code.year)[-2:]}-{str(ref_code.reference_number).zfill(7)}-01"
