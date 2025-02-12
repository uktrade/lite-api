from django.db import models
from django.db.models import Q

from model_utils.managers import InheritanceManager

from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class BaseApplicationManager(InheritanceManager):
    def drafts(self, organisation, sort_by):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().filter(status=draft, organisation=organisation).order_by(sort_by)

    def submitted(self, organisation, sort_by):
        finalised = get_case_status_by_status(CaseStatusEnum.FINALISED)
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return (
            self.get_queryset()
            .filter(organisation=organisation)
            .exclude(Q(status=draft) | Q(status=finalised))
            .order_by(sort_by)
        )

    def finalised(self, organisation, sort_by):
        finalised = get_case_status_by_status(CaseStatusEnum.FINALISED)
        return self.get_queryset().filter(status=finalised, organisation=organisation).order_by(sort_by)


class StandardApplicationQuerySet(models.QuerySet):
    def get_prepared_object(self, pk):
        return (
            self.select_related(
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
                "goods__goodonapplicationdocument_set",
                "goods__goodonapplicationdocument_set__user",
                "goods__good_on_application_internal_documents",
                "goods__good_on_application_internal_documents__document",
                "denial_matches",
                "denial_matches__denial_entity",
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
            .get(pk=pk)
        )
