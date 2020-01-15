from applications.enums import ApplicationType, ApplicationExportType
from static.countries.models import Country


def get_default_duration(application):
    """
    Returns default duration in months

    Rules defined in: https://uktrade.atlassian.net/browse/LT-1586
    """

    if application.export_type == ApplicationExportType.TEMPORARY:
        return 1 * 12

    if (
        application.application_type == ApplicationType.STANDARD_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        return 2 * 12

    if (
        application.application_type == ApplicationType.OPEN_LICENCE
        and application.export_type == ApplicationExportType.PERMANENT
    ):
        is_eu = Country.objects.filter(countries_on_application__application=application, is_eu=True).exists()
        return 3 * 12 if is_eu else 5 * 12
