from api.applications.enums import ApplicationExportType, DefaultDuration
from cases.enums import CaseTypeSubTypeEnum
from api.static.countries.models import Country


def get_default_duration(application):
    """
    Returns default duration in months

    Rules defined in: https://uktrade.atlassian.net/browse/LT-1586
    """
    # MOD clearance application do not have an export type
    if hasattr(application.baseapplication, "openapplication"):
        export_type = application.baseapplication.openapplication.export_type
    elif hasattr(application.baseapplication, "standardapplication"):
        export_type = application.baseapplication.standardapplication.export_type
    else:
        export_type = None

    if CaseTypeSubTypeEnum.is_mod_clearance(application.case_type.sub_type):
        return DefaultDuration.TEMPORARY.value

    elif export_type == ApplicationExportType.TEMPORARY:
        return DefaultDuration.TEMPORARY.value

    elif (
        application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD
        and export_type == ApplicationExportType.PERMANENT
    ):
        return DefaultDuration.PERMANENT_STANDARD.value

    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN and export_type == ApplicationExportType.PERMANENT:
        is_eu = Country.objects.filter(countries_on_application__application=application, is_eu=True).exists()
        return DefaultDuration.PERMANENT_OPEN_EU.value if is_eu else DefaultDuration.PERMANENT_OPEN.value
