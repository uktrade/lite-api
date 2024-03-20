from api.applications.enums import ApplicationExportType, DefaultDuration
from api.cases.enums import CaseTypeSubTypeEnum


def get_default_duration(application):
    """
    Returns default duration in months

    Rules defined in: https://uktrade.atlassian.net/browse/LT-1586
    """
    export_type = None
    if hasattr(application.baseapplication, "standardapplication"):
        export_type = application.baseapplication.standardapplication.export_type

    if CaseTypeSubTypeEnum.is_mod_clearance(application.case_type.sub_type):
        return DefaultDuration.TEMPORARY.value

    elif export_type == ApplicationExportType.TEMPORARY:
        return DefaultDuration.TEMPORARY.value

    elif (
        application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD
        and export_type == ApplicationExportType.PERMANENT
    ):
        return DefaultDuration.PERMANENT_STANDARD.value
