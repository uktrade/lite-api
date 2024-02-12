from rest_framework import permissions

from api.organisations.libraries.get_organisation import get_request_user_organisation_id


class IsPartyDocumentInOrganisation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.party.organisation_id == get_request_user_organisation_id(request)
