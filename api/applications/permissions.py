from rest_framework import permissions


class IsExporterInOrganisation(permissions.BasePermission):
    def has_permission(self, request, view):
        organisation = view.get_organisation()
        return request.user.exporteruser.is_in_organisation(organisation)
