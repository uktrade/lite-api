from rest_framework import permissions

from api.organisations.libraries.get_organisation import get_request_user_organisation_id


class IsCaseworkerOrInDocumentOrganisation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "govuser"):
            return True
        elif hasattr(request.user, "exporteruser"):
            # assume exporters will only be retrieving casedocuments
            if not obj.casedocument.visible_to_exporter:
                return False
            return obj.casedocument.case.organisation_id == get_request_user_organisation_id(request)
        raise NotImplementedError()
