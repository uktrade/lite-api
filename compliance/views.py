from uuid import UUID

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from audit_trail.models import Audit
from cases.libraries.get_case import get_case
from cases.models import Case
from compliance.helpers import (
    get_record_holding_sites_for_case,
    get_compliance_site_case,
    get_exporter_visible_compliance_site_cases,
)
from compliance.helpers import read_and_validate_csv, fetch_and_validate_licences
from compliance.models import OpenLicenceReturns, ComplianceVisitCase, CompliancePerson
from compliance.serializers.ComplianceSiteCaseSerializers import (
    ComplianceLicenceListSerializer,
    ExporterComplianceVisitListSerializer,
    ExporterComplianceVisitDetailSerializer,
    ExporterComplianceSiteListSerializer,
    ExporterComplianceSiteDetailSerializer,
)
from compliance.serializers.ComplianceVisitCaseSerializers import ComplianceVisitSerializer, CompliancePersonSerializer
from compliance.serializers.OpenLicenceReturns import (
    OpenLicenceReturnsCreateSerializer,
    OpenLicenceReturnsListSerializer,
    OpenLicenceReturnsViewSerializer,
)
from conf.authentication import GovAuthentication, ExporterAuthentication, SharedAuthentication
from lite_content.lite_api.strings import Compliance
from organisations.libraries.get_organisation import get_request_user_organisation_id, get_request_user_organisation
from users.libraries.notifications import get_compliance_site_case_notifications


class ExporterComplianceListSerializer(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExporterComplianceSiteListSerializer

    def get_queryset(self):
        return get_exporter_visible_compliance_site_cases(self.request, None)

    def get_paginated_response(self, data):
        data = get_compliance_site_case_notifications(data, self.request)
        return super().get_paginated_response(data)


class ExporterComplianceSiteDetailView(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExporterComplianceSiteDetailSerializer
    organisation = None

    def get_queryset(self):
        self.organisation = get_request_user_organisation(self.request)
        return get_exporter_visible_compliance_site_cases(self.request, self.organisation)

    def get_serializer_context(self):
        context = super().get_serializer_context()

        context["organisation"] = self.organisation
        return context


class ExporterVisitList(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExporterComplianceVisitListSerializer

    def get_queryset(self):
        return (
            ComplianceVisitCase.objects.select_related("case_officer")
            .filter(site_case_id=self.kwargs["pk"])
            .order_by("created_at")
        )

    def get_paginated_response(self, data):
        data = get_compliance_site_case_notifications(data, self.request)
        return super().get_paginated_response(data)


class ExporterVisitDetail(RetrieveAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = ExporterComplianceVisitDetailSerializer
    queryset = ComplianceVisitCase.objects.select_related("case_officer").all()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        organisation_id = get_request_user_organisation_id(self.request)

        context["organisation_id"] = organisation_id
        return context


class LicenceList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = ComplianceLicenceListSerializer

    def get_queryset(self):
        # For Compliance cases, when viewing from the site, we care about the Case the licence is attached to primarily,
        #   and the licence status (not added), and returns completed (not added).
        reference_code = self.request.GET.get("reference", "").upper()

        cases = Case.objects.filter_cases_with_compliance_related_licence_attached(self.kwargs["pk"])

        if reference_code:
            cases = cases.filter(reference_code__contains=reference_code)

        return cases

    def get_paginated_response(self, data):
        current_date = timezone.now().date()

        # We take an OLR as outstanding if it hasn't been added by the end of January, meaning if the
        # month is currently January we only go back 1 year
        olr_year = current_date.year - 2 if current_date.month == 1 else current_date.year - 1

        org_id = get_case(self.kwargs["pk"]).organisation_id
        licences_with_olr = set(
            OpenLicenceReturns.objects.filter(year=olr_year, organisation_id=org_id).values_list(
                "licences__application", flat=True
            )
        )

        for licence in data:
            licence["has_open_licence_returns"] = UUID(licence["id"]) in licences_with_olr

        return super().get_paginated_response(data)


class ComplianceSiteVisits(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)

    def post(self, request, *args, **kwargs):
        """
        Create a compliance visit case for a given compliance site case
        """
        pk = kwargs["pk"]
        site_case = get_compliance_site_case(pk)

        visit_case = site_case.create_visit_case()

        audit_trail_service.create(
            actor=request.user,
            verb=AuditType.COMPLIANCE_VISIT_CASE_CREATED,
            action_object=visit_case.get_case(),
            payload={},
        )

        return JsonResponse(
            data={"data": ComplianceVisitSerializer(instance=visit_case).data}, status=status.HTTP_201_CREATED
        )


class ComplianceVisitCaseView(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)
    queryset = ComplianceVisitCase.objects.all()
    serializer_class = ComplianceVisitSerializer

    def perform_update(self, serializer):
        fields = [
            ("visit_type", Compliance.ActivityFieldDisplay.VISIT_TYPE),
            ("overall_risk_value", Compliance.ActivityFieldDisplay.OVERALL_RISK_VALUE),
            ("licence_risk_value", Compliance.ActivityFieldDisplay.LICENCE_RISK_VALUE),
            ("overview", Compliance.ActivityFieldDisplay.OVERVIEW),
            ("inspection", Compliance.ActivityFieldDisplay.INSPECTION),
            ("compliance_overview", Compliance.ActivityFieldDisplay.COMPLIANCE_OVERVIEW),
            ("compliance_risk_value", Compliance.ActivityFieldDisplay.COMPLIANCE_RISK_VALUE),
            ("individuals_overview", Compliance.ActivityFieldDisplay.INDIVIDUALS_OVERVIEW),
            ("individuals_risk_value", Compliance.ActivityFieldDisplay.INDIVIDUALS_RISK_VALUE),
            ("products_overview", Compliance.ActivityFieldDisplay.PRODUCTS_OVERVIEW),
            ("products_risk_value", Compliance.ActivityFieldDisplay.PRODUCTS_RISK_VALUE),
        ]
        # data setup for audit checks
        original_instance = self.get_object()

        # save model
        updated_instance = serializer.save()

        audits = []
        case = updated_instance.get_case()
        for field, display in fields:
            if getattr(original_instance, field) != getattr(updated_instance, field):
                audits.append(
                    Audit(
                        actor=self.request.user,
                        verb=AuditType.COMPLIANCE_VISIT_CASE_UPDATED,
                        action_object=case,
                        payload={
                            "key": display,
                            "old": getattr(original_instance, field),
                            "new": getattr(updated_instance, field),
                        },
                    )
                )

        # handle dates separately in auditing since it requires different formatting
        if original_instance.visit_date != updated_instance.visit_date:
            old = original_instance.visit_date.strftime("%Y-%m-%d") if original_instance.visit_date else "Not set"
            audits.append(
                Audit(
                    actor=self.request.user,
                    verb=AuditType.COMPLIANCE_VISIT_CASE_UPDATED,
                    action_object=case,
                    payload={
                        "key": Compliance.ActivityFieldDisplay.VISIT_DATE,
                        "old": old,
                        "new": updated_instance.visit_date.strftime("%Y-%m-%d"),
                    },
                )
            )

        if audits:
            Audit.objects.bulk_create(audits)


class ComplianceCaseId(APIView):
    """
    This endpoint is currently only used for testing purposes.
    It gives us back the compliance case ids for the given case.
    """

    authentication_classes = (GovAuthentication,)

    def get(self, request, pk, *args, **kwargs):
        case = get_case(pk)
        # Get record holding sites for the case
        record_holding_sites_id = get_record_holding_sites_for_case(case)

        # Get list of record holding sites that do not have a compliance case
        existing_compliance_cases = Case.objects.filter(
            compliancesitecase__site_id__in=record_holding_sites_id
        ).distinct()

        return JsonResponse(
            data={"ids": list(existing_compliance_cases.values_list("id", flat=True))}, status=status.HTTP_200_OK
        )


class OpenLicenceReturnsView(ListAPIView):
    authentication_classes = (ExporterAuthentication,)
    serializer_class = OpenLicenceReturnsListSerializer

    def get_queryset(self):
        organisation_id = get_request_user_organisation_id(self.request)
        return OpenLicenceReturns.objects.filter(organisation_id=organisation_id).order_by("-year", "-created_at")

    def post(self, request):
        file = request.data.get("file")
        if not file:
            raise ValidationError({"file": [Compliance.OpenLicenceReturns.FILE_ERROR]})

        organisation_id = get_request_user_organisation_id(request)
        references, cleaned_text = read_and_validate_csv(file)
        licence_ids = fetch_and_validate_licences(references, organisation_id)

        data = request.data
        data["returns_data"] = cleaned_text
        data["licences"] = licence_ids
        data["organisation"] = organisation_id
        serializer = OpenLicenceReturnsCreateSerializer(data=data)

        if not serializer.is_valid():
            return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return JsonResponse(data={"open_licence_returns": serializer.data["id"]}, status=status.HTTP_201_CREATED)


class OpenLicenceReturnDownloadView(RetrieveAPIView):
    authentication_classes = (SharedAuthentication,)
    queryset = OpenLicenceReturns.objects.all()
    serializer_class = OpenLicenceReturnsViewSerializer


class ComplianceVisitPeoplePresentView(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = CompliancePersonSerializer

    def get_queryset(self):
        return CompliancePerson.objects.filter(visit_case_id=self.kwargs["pk"])

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        response = []

        # if people present is passed forward, we wish to validate and replace the current data
        if request.data.get("people_present"):
            serializer = self.get_serializer(data=request.data.get("people_present"), many=True,)
            serializer.is_valid(raise_exception=True)
            # We wish to replace the current people present with the new list of people present
            CompliancePerson.objects.filter(visit_case_id=self.kwargs["pk"]).delete()
            serializer.save(visit_case_id=self.kwargs["pk"])
            response = serializer.data
        else:
            # if no people present are given we remove all current people
            CompliancePerson.objects.filter(visit_case_id=self.kwargs["pk"]).delete()

        return JsonResponse(data={"people_present": response}, status=status.HTTP_201_CREATED)


class ComplianceVisitPersonPresentView(RetrieveUpdateDestroyAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = CompliancePersonSerializer
    queryset = CompliancePerson.objects.all()

    def perform_update(self, serializer):
        person = serializer.save()

        case = get_case(person.visit_case_id)

        audit_trail_service.create(
            actor=self.request.user,
            verb=AuditType.COMPLIANCE_PEOPLE_PRESENT_UPDATED,
            action_object=case,
            payload={"name": person.name, "job_title": person.job_title,},
        )

    def perform_destroy(self, instance):
        instance.delete()
        case = get_case(instance.visit_case_id)
        audit_trail_service.create(
            actor=self.request.user, verb=AuditType.COMPLIANCE_PEOPLE_PRESENT_DELETED, action_object=case, payload={},
        )
