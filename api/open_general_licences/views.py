from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView

from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.audit_trail.serializers import AuditSerializer
from api.core import constants
from api.core.authentication import SharedAuthentication, GovAuthentication
from api.core.helpers import str_to_bool
from api.core.permissions import assert_user_has_permission
from lite_content.lite_api.strings import OpenGeneralLicences
from api.open_general_licences.models import OpenGeneralLicence, OpenGeneralLicenceCase
from api.open_general_licences.serializers import OpenGeneralLicenceSerializer
from api.organisations.libraries.get_organisation import get_request_user_organisation
from api.organisations.models import Site
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import UserType
from api.users.models import GovUser, GovNotification


class OpenGeneralLicenceList(ListCreateAPIView):
    authentication_classes = (SharedAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = (
        OpenGeneralLicence.objects.all()
        .select_related("case_type")
        .prefetch_related("countries", "control_list_entries")
    )

    def get_serializer_context(self):
        user = self.request.user
        if hasattr(user, "exporteruser"):
            organisation = get_request_user_organisation(self.request)
            sites = Site.objects.get_by_user_and_organisation(self.request.user.exporteruser, organisation)
            cases = (
                OpenGeneralLicenceCase.objects.filter(site__in=sites)
                .select_related("status", "site", "site__address")
                .order_by("created_at")
                .annotate(records_located_at_name=F("site__site_records_located_at__name"))
            )

            if str_to_bool(self.request.GET.get("active_only")):
                cases = cases.filter(
                    status__status__in=[
                        CaseStatusEnum.FINALISED,
                        CaseStatusEnum.REGISTERED,
                        CaseStatusEnum.UNDER_ECJU_REVIEW,
                    ]
                )

            return {"user": user, "organisation": organisation, "cases": cases}

    def filter_queryset(self, queryset):
        filter_data = self.request.GET

        if self.request.user.type == UserType.INTERNAL:
            assert_user_has_permission(self.request.user.govuser, constants.GovPermissions.MAINTAIN_OGL)
        elif self.request.user.type == UserType.EXPORTER:
            if filter_data.get("site"):
                queryset = queryset.filter(cases__site_id=filter_data.get("site"))

            if str_to_bool(filter_data.get("active_only")):
                queryset = queryset.filter(
                    cases__status__status__in=[
                        CaseStatusEnum.FINALISED,
                        CaseStatusEnum.REGISTERED,
                        CaseStatusEnum.UNDER_ECJU_REVIEW,
                    ]
                )

            if str_to_bool(filter_data.get("registered")):
                organisation = get_request_user_organisation(self.request)
                sites = Site.objects.get_by_user_and_organisation(self.request.user.exporteruser, organisation)
                queryset = queryset.filter(cases__site__in=sites).distinct()

        if filter_data.get("name"):
            queryset = queryset.filter(name__icontains=filter_data.get("name"))

        if filter_data.get("case_type"):
            queryset = queryset.filter(case_type_id=filter_data.get("case_type"))

        if filter_data.get("control_list_entry"):
            queryset = queryset.filter(control_list_entries__rating=filter_data.get("control_list_entry"))

        if filter_data.get("country"):
            queryset = queryset.filter(countries__id__contains=filter_data.get("country"))

        if filter_data.get("status"):
            queryset = queryset.filter(status=filter_data.get("status"))

        return queryset

    def perform_create(self, serializer):
        assert_user_has_permission(self.request.user.govuser, constants.GovPermissions.MAINTAIN_OGL)

        if not self.request.data.get("validate_only", False):
            instance = serializer.save()

            audit_trail_service.create(
                actor=self.request.user, verb=AuditType.OGL_CREATED, action_object=instance,
            )


class OpenGeneralLicenceDetail(RetrieveUpdateAPIView):
    authentication_classes = (SharedAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = (
        OpenGeneralLicence.objects.all()
        .select_related("case_type")
        .prefetch_related("countries", "control_list_entries")
    )

    def get_serializer_context(self):
        user = self.request.user
        if user.type == UserType.EXPORTER:
            organisation = get_request_user_organisation(self.request)
            sites = Site.objects.get_by_user_and_organisation(self.request.user.exporteruser, organisation)
            cases = (
                OpenGeneralLicenceCase.objects.filter(site__in=sites)
                .select_related("status", "site", "site__address")
                .annotate(records_located_at_name=F("site__site_records_located_at__name"))
            )

            return {"user": user, "organisation": organisation, "cases": cases}

    def perform_update(self, serializer):
        assert_user_has_permission(self.request.user.govuser, constants.GovPermissions.MAINTAIN_OGL)

        # Don't update the data during validate_only requests
        if not self.request.data.get("validate_only", False):
            fields = [
                ("name", OpenGeneralLicences.ActivityFieldDisplay.NAME),
                ("description", OpenGeneralLicences.ActivityFieldDisplay.DESCRIPTION),
                ("url", OpenGeneralLicences.ActivityFieldDisplay.URL),
                ("case_type", OpenGeneralLicences.ActivityFieldDisplay.CASE_TYPE),
                ("registration_required", OpenGeneralLicences.ActivityFieldDisplay.REGISTRATION_REQUIRED),
                ("status", OpenGeneralLicences.ActivityFieldDisplay.STATUS),
            ]
            m2m_fields = [
                ("countries", OpenGeneralLicences.ActivityFieldDisplay.COUNTRIES),
                ("control_list_entries", OpenGeneralLicences.ActivityFieldDisplay.CONTROL_LIST_ENTRIES),
            ]
            # data setup for audit checks
            original_instance = self.get_object()
            original_m2m_sets = {}
            for field, display in m2m_fields:
                original_m2m_sets[field] = set(getattr(original_instance, field).all())

            # save model
            updated_instance = serializer.save()

            for field, display in fields:
                if getattr(original_instance, field) != getattr(updated_instance, field):
                    audit_trail_service.create(
                        actor=self.request.user,
                        verb=AuditType.OGL_FIELD_EDITED,
                        action_object=updated_instance,
                        payload={
                            "key": display,
                            "old": getattr(original_instance, field),
                            "new": getattr(updated_instance, field),
                        },
                    )

            for field, display in m2m_fields:
                if original_m2m_sets[field] != set(getattr(updated_instance, field).all()):
                    audit_trail_service.create(
                        actor=self.request.user,
                        verb=AuditType.OGL_MULTI_FIELD_EDITED,
                        action_object=updated_instance,
                        payload={"key": display},
                    )


class OpenGeneralLicenceActivityView(APIView):
    authentication_classes = (GovAuthentication,)

    def get(self, request, pk):
        assert_user_has_permission(request.user.govuser, constants.GovPermissions.MAINTAIN_OGL)
        filter_data = audit_trail_service.get_filters(request.GET)
        content_type = ContentType.objects.get_for_model(OpenGeneralLicence)
        audit_trail_qs = audit_trail_service.filter_object_activity(
            object_id=pk, object_content_type=content_type, **filter_data
        )

        data = AuditSerializer(audit_trail_qs, many=True).data

        if isinstance(request.user, GovUser):
            # Delete notifications related to audits
            GovNotification.objects.filter(user_id=request.user.pk, object_id__in=[obj["id"] for obj in data]).delete()

        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"activity": data, "filters": filters}, status=status.HTTP_200_OK)
