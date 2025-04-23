from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from api.core.authentication import GovAuthentication
from api.core.exceptions import NotFoundError
from api.applications.libraries.get_applications import get_application


class CaseworkerApplicationMixin:
    authentication_classes = (GovAuthentication,)

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()

    def get_object(self):
        self.check_object_permissions(self.request, self.application)
        return self.application

    def get_case(self):
        return self.application
