from datetime import datetime
from typing import List

from compat import get_model
from django.db import models, transaction
from django.db.models import Q, Case, When, BinaryField
from django.utils import timezone

from cases.enums import AdviceLevel, CaseTypeEnum
from cases.helpers import get_updated_case_ids, get_assigned_to_user_case_ids, get_assigned_as_case_officer_case_ids
from api.common.enums import SortOrder
from api.compliance.enums import COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
from licences.enums import LicenceStatus
from queues.constants import (
    ALL_CASES_QUEUE_ID,
    MY_TEAMS_QUEUES_CASES_ID,
    OPEN_CASES_QUEUE_ID,
    UPDATED_CASES_QUEUE_ID,
    MY_ASSIGNED_CASES_QUEUE_ID,
    MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID,
)
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_by_status


class CaseQuerySet(models.QuerySet):
    """
    Custom queryset for the Case model. This allows us to chain application specific
    filtering logic in a reusable way.

    For example:

    To get all open cases within a specific queue:
       > qs = Case.objects.is_open().in_queue('0001')
    """

    def is_open(self):
        return self.filter(status__is_terminal=False)

    def in_queues(self, queues: List):
        return self.filter(queues__in=queues)

    def in_queue(self, queue_id):
        return self.filter(queues__in=[queue_id])

    def in_team(self, team_id):
        return self.filter(queues__team_id=team_id).distinct()

    def is_updated(self, user):
        """
        Get the cases that have raised notifications when updated by an exporter
        """
        updated_case_ids = get_updated_case_ids(user)
        return self.filter(id__in=updated_case_ids)

    def assigned_to_user(self, user):
        assigned_to_user_case_ids = get_assigned_to_user_case_ids(user)
        return self.filter(id__in=assigned_to_user_case_ids)

    def not_assigned_to_any_user(self):
        return self.filter(case_assignments=None)

    def assigned_as_case_officer(self, user):
        assigned_as_case_officer_case_ids = get_assigned_as_case_officer_case_ids(user)
        return self.filter(id__in=assigned_as_case_officer_case_ids)

    def not_terminal(self):
        return self.filter(status__is_terminal=False)

    def has_status(self, status):
        return self.filter(status__status=status)

    def is_type(self, case_type):
        return self.filter(case_type=case_type)

    def with_case_reference_code(self, case_reference):
        return self.filter(reference_code__icontains=case_reference)

    def with_exporter_application_reference(self, exporter_application_reference):
        return self.filter(baseapplication__name__icontains=exporter_application_reference)

    def with_organisation(self, organisation_name):
        return self.filter(organisation__name__icontains=organisation_name)

    def with_exporter_site_name(self, exporter_site_name):
        return self.filter(baseapplication__application_sites__site__name=exporter_site_name)

    def with_sla_days_elapsed(self, sla_days_elapsed):
        return self.filter(sla_days=sla_days_elapsed)

    def with_exporter_site_address(self, exporter_site_address):
        return self.filter(
            Q(baseapplication__application_sites__site__address__address_line_1__icontains=exporter_site_address)
            | Q(baseapplication__application_sites__site__address__address_line_2__icontains=exporter_site_address)
            | Q(baseapplication__application_sites__site__address__region__icontains=exporter_site_address)
            | Q(baseapplication__application_sites__site__address__region__icontains=exporter_site_address)
            | Q(baseapplication__application_sites__site__address__postcode__icontains=exporter_site_address)
            | Q(baseapplication__application_sites__site__address__address__icontains=exporter_site_address)
        )

    def with_control_list_entry(self, control_list_entry):
        return self.filter(
            Q(baseapplication__goods__good__control_list_entries__rating__in=[control_list_entry])
            | Q(baseapplication__goods_type__control_list_entries__rating__in=[control_list_entry])
        )

    def with_flags(self, flags):
        case_flag_ids = self.filter(flags__id__in=flags).values_list("id", flat=True)
        org_flag_ids = self.filter(organisation__flags__id__in=flags).values_list("id", flat=True)
        open_flag_ids = self.filter(
            baseapplication__openapplication__application_countries__country__flags__id__in=flags
        ).values_list("id", flat=True)
        goods_flag_ids = self.filter(baseapplication__goods__good__flags__id__in=flags).values_list("id", flat=True)
        goods_type_flag_ids = self.filter(baseapplication__goods_type__flags__id__in=flags).values_list("id", flat=True)

        case_ids = set(
            list(case_flag_ids)
            + list(org_flag_ids)
            + list(open_flag_ids)
            + list(goods_flag_ids)
            + list(goods_type_flag_ids)
        )
        return self.filter(id__in=case_ids)

    def with_country(self, country_id):
        return self.filter(
            Q(baseapplication__parties__party__country_id=country_id)
            | Q(baseapplication__openapplication__application_countries__country_id=country_id)
        )

    def with_advice(self, advice_type, level):
        return self.filter(advice__type=advice_type, advice__level=level)

    def with_sla_days_range(self, min_sla, max_sla):
        qs = self.filter()
        if min_sla:
            qs = qs.filter(sla_remaining_days__gte=int(min_sla))
        if max_sla:
            qs = qs.filter(sla_remaining_days__lte=int(max_sla))
        return qs

    def with_submitted_range(self, submitted_from, submitted_to):
        qs = self.filter()
        if submitted_from:
            qs = qs.filter(submitted_at__date__gte=submitted_from)
        if submitted_to:
            qs = qs.filter(submitted_at__date__lte=submitted_to)
        return qs

    def with_finalised_range(self, finalised_from, finalised_to):
        qs = self.filter(status__status=CaseStatusEnum.FINALISED)
        if finalised_from:
            qs = qs.filter(advice__level=AdviceLevel.FINAL, advice__created_at__date__gte=finalised_from)
        if finalised_to:
            qs = qs.filter(advice__level=AdviceLevel.FINAL, advice__created_at__date__lte=finalised_to)
        return qs

    def with_party_name(self, party_name):
        return self.filter(baseapplication__parties__party__name__icontains=party_name)

    def with_party_address(self, party_address):
        return self.filter(baseapplication__parties__party__address__icontains=party_address)

    def with_goods_related_description(self, goods_related_description):
        return self.filter(
            Q(baseapplication__goods__good__description__icontains=goods_related_description)
            | Q(baseapplication__goods__good__comment__icontains=goods_related_description)
            | Q(baseapplication__goods__good__report_summary__icontains=goods_related_description)
            | Q(baseapplication__goods_type__description__icontains=goods_related_description)
            | Q(baseapplication__goods_type__comment__icontains=goods_related_description)
            | Q(baseapplication__goods_type__report_summary__icontains=goods_related_description)
        )

    def order_by_date(self, order="-"):
        """
        :param order: ('', '-')
        :return:
        """
        order = order if order in ["", "-"] else ""

        return self.order_by(f"{order}submitted_at")

    def filter_based_on_queue(self, queue_id, team_id, user):
        if queue_id == MY_TEAMS_QUEUES_CASES_ID:
            return self.in_team(team_id=team_id)
        elif queue_id == OPEN_CASES_QUEUE_ID:
            return self.is_open()
        elif queue_id == UPDATED_CASES_QUEUE_ID:
            return self.is_updated(user=user)
        elif queue_id == MY_ASSIGNED_CASES_QUEUE_ID:
            return self.assigned_to_user(user=user).not_terminal()
        elif queue_id == MY_ASSIGNED_AS_CASE_OFFICER_CASES_QUEUE_ID:
            return self.assigned_as_case_officer(user=user).not_terminal()
        elif queue_id is not None and queue_id != ALL_CASES_QUEUE_ID:
            return self.in_queue(queue_id=queue_id)

        return self


class CaseManager(models.Manager):
    """
    Custom manager for the Case model that uses CaseQuerySet and provides a reusable search
    functionality to the Case model.
    """

    NOT_ASSIGNED = "not_assigned"

    def get_queryset(self):
        return CaseQuerySet(self.model, using=self.db)

    def search(  # noqa
        self,
        queue_id=None,
        is_work_queue=None,
        user=None,
        status=None,
        case_type=None,
        assigned_user=None,
        case_officer=None,
        include_hidden=None,
        organisation_name=None,
        case_reference=None,  # gov case number
        exporter_application_reference=None,
        exporter_site_name=None,
        exporter_site_address=None,
        control_list_entry=None,
        flags=None,
        country=None,
        team_advice_type=None,
        final_advice_type=None,
        min_sla_days_remaining=None,
        max_sla_days_remaining=None,
        submitted_from=None,
        submitted_to=None,
        finalised_from=None,
        finalised_to=None,
        party_name=None,
        party_address=None,
        goods_related_description=None,
        sla_days_elapsed_sort_order=None,
        sla_days_elapsed=None,
        **kwargs,
    ):
        """
        Search for a user's available cases given a set of search parameters.
        """
        case_qs = (
            self.submitted()
            .select_related("status", "case_type")
            .prefetch_related("case_assignments", "case_assignments__user", "case_assignments__queue",)
        )

        if not include_hidden and user:
            EcjuQuery = get_model("cases", "ecjuquery")
            CaseReviewDate = get_model("cases", "casereviewdate")

            case_qs = case_qs.exclude(
                id__in=EcjuQuery.objects.filter(raised_by_user__team_id=user.team.id, responded_at__isnull=True)
                .values("case_id")
                .distinct()
            )

            # We hide cases that have a next review date that is set in the future (for your team)
            case_qs = case_qs.exclude(
                id__in=CaseReviewDate.objects.filter(
                    team_id=user.team.id, next_review_date__gt=timezone.localtime().date()
                ).values("case_id")
            )

        if queue_id and user:
            case_qs = case_qs.filter_based_on_queue(queue_id=queue_id, team_id=user.team.id, user=user)

        if status:
            case_qs = case_qs.has_status(status=status)

        if case_type:
            case_type = CaseTypeEnum.reference_to_id(case_type)
            case_qs = case_qs.is_type(case_type=case_type)

        if assigned_user:
            if assigned_user == self.NOT_ASSIGNED:
                case_qs = case_qs.not_assigned_to_any_user()
            else:
                case_qs = case_qs.assigned_to_user(user=assigned_user)

        if case_officer:
            if case_officer == self.NOT_ASSIGNED:
                case_officer = None
            case_qs = case_qs.assigned_as_case_officer(user=case_officer)

        if case_reference:
            case_qs = case_qs.with_case_reference_code(case_reference)

        if exporter_application_reference:
            case_qs = case_qs.with_exporter_application_reference(exporter_application_reference)

        if organisation_name:
            case_qs = case_qs.with_organisation(organisation_name)

        if exporter_site_name:
            case_qs = case_qs.with_exporter_site_name(exporter_site_name)

        if exporter_site_address:
            case_qs = case_qs.with_exporter_site_address(exporter_site_address)

        if control_list_entry:
            case_qs = case_qs.with_control_list_entry(control_list_entry)

        if flags:
            case_qs = case_qs.with_flags(flags)

        if country:
            case_qs = case_qs.with_country(country)

        if team_advice_type:
            case_qs = case_qs.with_advice(team_advice_type, AdviceLevel.TEAM)

        if final_advice_type:
            case_qs = case_qs.with_advice(final_advice_type, AdviceLevel.FINAL)

        if min_sla_days_remaining or max_sla_days_remaining:
            case_qs = case_qs.with_sla_days_range(min_sla=min_sla_days_remaining, max_sla=max_sla_days_remaining)

        if sla_days_elapsed:
            case_qs = case_qs.with_sla_days_elapsed(sla_days_elapsed)

        if submitted_from or submitted_to:
            case_qs = case_qs.with_submitted_range(submitted_from=submitted_from, submitted_to=submitted_to)

        if finalised_from or finalised_to:
            case_qs = case_qs.with_finalised_range(finalised_from=finalised_from, finalised_to=finalised_to)

        if party_name:
            case_qs = case_qs.with_party_name(party_name)

        if party_address:
            case_qs = case_qs.with_party_address(party_address)

        if goods_related_description:
            case_qs = case_qs.with_goods_related_description(goods_related_description)

        if is_work_queue:
            case_qs = case_qs.annotate(
                case_order=Case(
                    When(baseapplication__hmrcquery__have_goods_departed=False, then=0),
                    default=1,
                    output_field=BinaryField(),
                )
            )

            case_qs = case_qs.order_by("case_order", "submitted_at")
        else:
            case_qs = case_qs.order_by_date()

        if sla_days_elapsed_sort_order:
            if sla_days_elapsed_sort_order == SortOrder.ASCENDING:
                case_qs = case_qs.order_by("sla_days")
            else:
                case_qs = case_qs.order_by("-sla_days")

        return case_qs.distinct()

    def submitted(self):
        draft = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return self.get_queryset().exclude(status=draft)

    def get_application(self, case):
        from api.applications.models import StandardApplication

        try:
            return StandardApplication.objects.get(baseapplication_ptr__case_ptr=case)
        except StandardApplication.DoesNotExist:
            pass

        from api.applications.models import OpenApplication

        try:
            return OpenApplication.objects.get(baseapplication_ptr__case_ptr=case)
        except OpenApplication.DoesNotExist:
            pass

        raise Exception(f"Application object not found from case: {case}")

    def get_query(self, case):
        from api.queries.goods_query.models import GoodsQuery

        try:
            return GoodsQuery.objects.get(query_ptr__case_ptr=case)
        except GoodsQuery.DoesNotExist:
            pass

        from api.queries.end_user_advisories.models import EndUserAdvisoryQuery

        try:
            return EndUserAdvisoryQuery.objects.get(query_ptr__case_ptr=case)
        except EndUserAdvisoryQuery.DoesNotExist:
            pass

        raise Exception(f"Query object not found from case: {case}")

    def get_obj(self, case):
        application = self.get_application(case)
        if application:
            return application

        query = self.get_query(case)
        if query:
            return query

        return case

    def filter_for_cases_related_to_compliance_case(self, compliance_case_id):
        """
        :return a list of cases in a queryset object which are linked to the compliance case id given.
        """

        # We filter cases to look at if an object contains an non-draft licence (if required)
        queryset = self.filter(
            Q(
                baseapplication__licences__status__in=[
                    LicenceStatus.ISSUED,
                    LicenceStatus.REINSTATED,
                    LicenceStatus.REVOKED,
                    LicenceStatus.SUSPENDED,
                    LicenceStatus.SURRENDERED,
                    LicenceStatus.CANCELLED,
                ],
                baseapplication__application_sites__site__site_records_located_at__compliance__id=compliance_case_id,
            )
            | Q(opengenerallicencecase__site__site_records_located_at__compliance__id=compliance_case_id)
        )

        # We filter for OIEL, OICL, OGLs, and specific SIELs (dependant on CLC codes present) as these are the only case
        #   types relevant for compliance cases
        GoodOnLicence = get_model("licences", "GoodOnLicence")
        approved_goods_on_licence = GoodOnLicence.objects.filter(
            good__good__control_list_entries__rating__regex=COMPLIANCE_CASE_ACCEPTABLE_GOOD_CONTROL_CODES
        ).values_list("good", flat=True)

        queryset = queryset.filter(
            case_type__id__in=[CaseTypeEnum.OICL.id, CaseTypeEnum.OIEL.id, *CaseTypeEnum.OPEN_GENERAL_LICENCE_IDS]
        ) | queryset.filter(baseapplication__goods__id__in=approved_goods_on_licence,)

        return queryset.distinct()


class CaseReferenceCodeManager(models.Manager):
    def create(self):
        CaseReferenceCode = self.model
        year = timezone.make_aware(datetime.now()).year

        # transaction.atomic is required to lock the database (which is achieved using select_for_update)
        #  we lock the case reference code record so that multiple cases being assigned a record don't end up with same
        #  number if both access function at same time.
        with transaction.atomic():
            case_reference_code, _ = CaseReferenceCode.objects.select_for_update().get_or_create(
                defaults={"year": year, "reference_number": 0}
            )

            if case_reference_code.year != year:
                case_reference_code.year = year
                case_reference_code.reference_number = 1
            else:
                case_reference_code.reference_number += 1

            case_reference_code.save()

        return case_reference_code


class AdviceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("created_at").prefetch_related(*self.model.ENTITY_FIELDS)

    def get_user_advice(self, case):
        return self.get_queryset().filter(case=case, level=AdviceLevel.USER)

    def get_team_advice(self, case, team=None):
        queryset = self.get_queryset().filter(case=case, level=AdviceLevel.TEAM)
        if team:
            queryset.filter(team=team)
        return queryset

    def get_final_advice(self, case):
        return self.get_queryset().filter(case=case, level=AdviceLevel.FINAL)

    def get(self, *args, **kwargs):
        """
        Override the default `get` on a queryset so that an additional, non-model-field argument (entity_id) can be
        supplied to the filter.
        """
        entity_id = kwargs.pop("entity_id", None)

        if entity_id:
            query = Q()

            for entity in self.model.ENTITY_FIELDS:
                query.add(Q(**{entity: entity_id}), Q.OR)

            return super().filter(query).get(*args, **kwargs)

        return super().get(*args, **kwargs)
