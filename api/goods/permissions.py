from rest_framework import permissions

from api.goods.enums import GoodStatus
from api.organisations.libraries.get_organisation import get_request_user_organisation_id


class IsDocumentInOrganisation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.good.organisation_id == get_request_user_organisation_id(request)


class IsGoodDraft(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.good.status == GoodStatus.DRAFT
