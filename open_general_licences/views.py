from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView

from audit_trail.enums import AuditType
from audit_trail import service as audit_trail_service
from conf.authentication import GovAuthentication
from open_general_licences.models import OpenGeneralLicence
from open_general_licences.serializers import OpenGeneralLicenceSerializer


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
            filtered_qs = filtered_qs.filter(control_list_entries_id__contains=filter_data.get("control_list_entry"))

        if filter_data.get("country"):
            filtered_qs = filtered_qs.filter(countries_id__contains=filter_data.get("country"))

        if filter_data.get("status"):
            filtered_qs = filtered_qs.filter(status=filter_data.get("status"))

        return filtered_qs

    def perform_create(self, serializer):
        instance = serializer.save()

        audit_trail_service.create(
            actor=self.request.user, verb=AuditType.CREATED, action_object=instance,
        )


class OpenGeneralLicenceDetail(RetrieveUpdateAPIView):
    authentication_classes = (GovAuthentication,)
    serializer_class = OpenGeneralLicenceSerializer
    queryset = OpenGeneralLicence.objects.all()
