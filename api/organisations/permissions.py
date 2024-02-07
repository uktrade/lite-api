from rest_framework import permissions

from api.organisations.libraries.get_organisation import get_request_user_organisation_id


class IsCaseworkerOrInDocumentOrganisation(permissions.BasePermission):
    def has_permission(self, request, view):
        if hasattr(request.user, "govuser"):
            return True
        elif hasattr(request.user, "exporteruser"):
            return view.kwargs["pk"] == get_request_user_organisation_id(request)
        raise NotImplementedError()

    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, "govuser"):
            return True
        elif hasattr(request.user, "exporteruser"):
            return obj.organisation_id == get_request_user_organisation_id(request)
        raise NotImplementedError()
