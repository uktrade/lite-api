from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from api.core.authentication import GovAuthentication
from api.core.exceptions import NotFoundError
from api.applications.libraries.get_applications import get_application
from api.f680.caseworker import filters


class F680CaseworkerApplicationMixin:
    authentication_classes = (GovAuthentication,)
    filter_backends = (filters.CurrentCaseFilter,)

    def dispatch(self, request, *args, **kwargs):
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

        return super().dispatch(request, *args, **kwargs)

    def get_case(self):
        return self.application
