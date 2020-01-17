from applications.enums import ApplicationType, ApplicationExportType
from static.countries.models import Country


class DefaultDuration:
    TEMPORARY = 1 * 12
    PERMANENT_STANDARD = 2 * 12
    PERMANENT_OPEN = 3 * 12
    PERMANENT_OPEN_EU = 5 * 12


def get_default_duration(application):
    """
    Returns default duration in months

    Rules defined in: https://uktrade.atlassian.net/browse/LT-1586
    """

    if application.export_type == ApplicationExportType.TEMPORARY:
        return DefaultDuration.TEMPORARY

    elif (
        application.application_type == ApplicationType.STANDARD_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        return DefaultDuration.PERMANENT_STANDARD

    elif (
        application.application_type == ApplicationType.OPEN_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        is_eu = Country.objects.filter(countries_on_application__application=application, is_eu=True).exists()
        return DefaultDuration.PERMANENT_OPEN_EU if is_eu else DefaultDuration.PERMANENT_OPEN
