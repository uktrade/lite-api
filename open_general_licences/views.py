from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView

from audit_trail.enums import AuditType
from audit_trail import service as audit_trail_service
from audit_trail.serializers import AuditSerializer
from conf import constants
from conf.authentication import GovAuthentication
from conf.permissions import assert_user_has_permission
from open_general_licences.models import OpenGeneralLicence
from open_general_licences.serializers import OpenGeneralLicenceSerializer
from users.models import GovUser, GovNotification
from lite_content.lite_api.strings import OpenGeneralLicences


class OpenGeneralLicenceList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = (
        OpenGeneralLicence.objects.all()
        .select_related("case_type")
        .prefetch_related("countries", "control_list_entries")
    )

    def initial(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.MAINTAIN_OGL)
        super(OpenGeneralLicenceList, self).initial(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        filtered_qs = queryset
        filter_data = self.request.GET

        if filter_data.get("name"):
            filtered_qs = filtered_qs.filter(name__icontains=filter_data.get("name"))

        if filter_data.get("case_type"):
            filtered_qs = filtered_qs.filter(case_type_id=filter_data.get("case_type"))

        if filter_data.get("control_list_entry"):
            filtered_qs = filtered_qs.filter(
                control_list_entries__rating__contains=filter_data.get("control_list_entry")
            )

        if filter_data.get("country"):
            filtered_qs = filtered_qs.filter(countries__id__contains=filter_data.get("country"))

        filtered_qs = filtered_qs.filter(status=filter_data.get("status", "active"))

        return filtered_qs

    def perform_create(self, serializer):
        if not self.request.data.get("validate_only", False):
            instance = serializer.save()

            audit_trail_service.create(
                actor=self.request.user, verb=AuditType.OGL_CREATED, action_object=instance,
            )


class OpenGeneralLicenceDetail(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = (
        OpenGeneralLicence.objects.all()
        .select_related("case_type")
        .prefetch_related("countries", "control_list_entries")
    )

    def initial(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.MAINTAIN_OGL)
        super(OpenGeneralLicenceDetail, self).initial(request, *args, **kwargs)

    def perform_update(self, serializer):
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
        assert_user_has_permission(request.user, constants.GovPermissions.MAINTAIN_OGL)
        filter_data = audit_trail_service.get_filters(request.GET)
        content_type = ContentType.objects.get_for_model(OpenGeneralLicence)
        audit_trail_qs = audit_trail_service.filter_object_activity(
            object_id=pk, object_content_type=content_type, **filter_data
        )

        data = AuditSerializer(audit_trail_qs, many=True).data

        if isinstance(request.user, GovUser):
            # Delete notifications related to audits
            GovNotification.objects.filter(user=request.user, object_id__in=[obj["id"] for obj in data]).delete()

        filters = audit_trail_service.get_objects_activity_filters(pk, content_type)

        return JsonResponse(data={"activity": data, "filters": filters}, status=status.HTTP_200_OK)
