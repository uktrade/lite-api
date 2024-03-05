from api.applications.models import (
    BaseApplication,
    OpenApplication,
    StandardApplication,
)
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.exceptions import NotFoundError


def get_application(pk, organisation_id=None):
    kwargs = {}
    if organisation_id:
        kwargs["organisation_id"] = str(organisation_id)

    application_type = _get_application_type(pk)

    try:
        if application_type == CaseTypeSubTypeEnum.STANDARD:
            qs = StandardApplication.objects.select_related(
                "baseapplication_ptr",
                "baseapplication_ptr__end_user",
                "baseapplication_ptr__end_user__party",
                "case_officer",
                "case_officer__team",
                "case_type",
                "organisation",
                "organisation__primary_site",
                "status",
                "submitted_by",
                "submitted_by__baseuser_ptr",
            ).prefetch_related(
                "goods",
                "goods__control_list_entries",
                "goods__good",
                "goods__good__control_list_entries",
                "goods__good__flags",
                "goods__good__flags__team",
                "goods__good__gooddocument_set",
                "goods__good__firearm_details",
                "goods__good__pv_grading_details",
                "goods__good__goods_on_application",
                "goods__good__goods_on_application__application",
                "goods__good__goods_on_application__application__queues",
                "goods__good__goods_on_application__good",
                "goods__good__goods_on_application__good__flags",
                "goods__good__goods_on_application__regime_entries",
                "goods__good__goods_on_application__regime_entries__subsection",
                "goods__good__goods_on_application__regime_entries__subsection__regime",
                "goods__regime_entries",
                "goods__regime_entries__subsection",
                "goods__regime_entries__subsection__regime",
                "goods__good__report_summary_prefix",
                "goods__good__report_summary_subject",
                "goods__audit_trail",
                "goods__goodonapplicationdocument_set",
                "goods__goodonapplicationdocument_set__user",
                "goods__good_on_application_internal_documents",
                "goods__good_on_application_internal_documents__document",
                "denial_matches",
                "denial_matches__denial",
                "application_sites",
                "application_sites__site",
                "application_sites__site__address",
                "application_sites__site__address__country",
                "external_application_sites",
                "applicationdocument_set",
                "goods__report_summary_prefix",
                "goods__report_summary_subject",
                "goods__firearm_details",
                "goods__assessed_by",
            )
            obj = qs.get(pk=pk, **kwargs)
            return obj
        elif application_type == CaseTypeSubTypeEnum.OPEN:
            return OpenApplication.objects.get(pk=pk, **kwargs)
        else:
            raise NotImplementedError(f"get_application does not support this application type: {application_type}")
    except (
        StandardApplication.DoesNotExist,
        OpenApplication.DoesNotExist,
    ):
        raise NotFoundError({"application": "Application not found - " + str(pk)})


def _get_application_type(pk):
    try:
        return BaseApplication.objects.values_list("case_type__sub_type", flat=True).get(pk=pk)
    except BaseApplication.DoesNotExist:
        raise NotFoundError({"application_type": "Application type not found - " + str(pk)})
