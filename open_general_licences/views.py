from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.views import APIView

from audit_trail.enums import AuditType
from audit_trail import service as audit_trail_service
from audit_trail.models import Audit
from audit_trail.serializers import AuditSerializer
from conf.authentication import GovAuthentication
from open_general_licences.models import OpenGeneralLicence
from open_general_licences.serializers import OpenGeneralLicenceSerializer
from users.models import GovUser, GovNotification


class OpenGeneralLicenceList(ListCreateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = OpenGeneralLicence.objects.all()

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

        if filter_data.get("status"):
            filtered_qs = filtered_qs.filter(status=filter_data.get("status"))

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
    queryset = OpenGeneralLicence.objects.all()

    def perform_update(self, serializer):
        # Don't update the data during validate_only requests
        if not self.request.data.get("validate_only", False):
            fields = [
                "name",
                "description",
                "url",
                "case_type",
                "registration_required",
                "status",
            ]
            m2m_fields = [
                "countries",
                "control_list_entries",
            ]
            # data setup for audit checks
            original_instance = self.get_object()
            original_m2m_sets = {}
            for field in m2m_fields:
                original_m2m_sets[field] = set(getattr(original_instance, field).all())

            # save model
            updated_instance = serializer.save()

            for field in fields:
                if getattr(original_instance, field) != getattr(updated_instance, field):
                    audit_trail_service.create(
                        actor=self.request.user,
                        verb=AuditType.OGL_FIELD_EDITED,
                        action_object=updated_instance,
                        payload={"field": field},
                    )

            for field in m2m_fields:
                if original_m2m_sets[field] != set(getattr(updated_instance, field).all()):
                    audit_trail_service.create(
                        actor=self.request.user,
                        verb=AuditType.OGL_FIELD_EDITED,
                        action_object=updated_instance,
                        payload={"field": field},
                    )


class OpenGeneralLicenceActivityView(APIView):
    def get(self, request, pk):
        audit_trail_qs = Audit.objects.filter(
            action_object_content_type=ContentType.objects.get_for_model(OpenGeneralLicenceSerializer),
            action_object_object_id=pk,
        ).all()

        data = AuditSerializer(audit_trail_qs, many=True).data

        if isinstance(request.user, GovUser):
            # Delete notifications related to audits
            GovNotification.objects.filter(user=request.user, object_id__in=[obj["id"] for obj in data]).delete()

        return JsonResponse(data={"activity": data}, status=status.HTTP_200_OK)
