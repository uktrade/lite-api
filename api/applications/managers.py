from model_utils.managers import InheritanceManager

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class BaseApplicationManager(InheritanceManager):
    def drafts(self, organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, organisation=organisation).order_by("-created_at")

    def submitted(self, organisation):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(organisation=organisation).exclude(status=draft).order_by("-submitted_at")

    def get_application(self, pk, **kwargs):
        raise NotImplementedError(f"get_application not implemented for {self.__class__.__name__}")


class StandardApplicationManager(BaseApplicationManager):
    def get_application(self, pk, **kwargs):
        qs = (
            self.get_queryset()
            .select_related(
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
            )
            .prefetch_related(
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
        )
        obj = qs.get(pk=pk, **kwargs)
        return obj


class OpenApplicationManager(BaseApplicationManager):
    def get_application(self, pk, **kwargs):
        qs = (
            self.get_queryset()
            .select_related(
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
            )
            .prefetch_related(
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
        )
        obj = qs.get(pk=pk, **kwargs)
        return obj


class F680ApplicationManager(BaseApplicationManager):
    def get_application(self, pk, **kwargs):
        qs = (
            self.get_queryset()
            .select_related(
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
            )
            .prefetch_related(
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
        )
        obj = qs.get(pk=pk, **kwargs)
        return obj
