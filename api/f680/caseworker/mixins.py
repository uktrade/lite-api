from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from api.core.authentication import GovAuthentication
from api.core.exceptions import NotFoundError
from api.applications.libraries.get_applications import get_application
from api.f680.caseworker import filters
from mohawk.exc import MisComputedContentHash as DoubleRequestException


class F680CaseworkerApplicationMixin:
    authentication_classes = (GovAuthentication,)
    filter_backends = (filters.CurrentCaseFilter, filters.F680CaseFilter)

    def initial(self, request, *args, **kwargs):
        """
        Below we are catching a situation where there is a post request inside of which auth
        is performed and therefore we get a hawk exception due to the first post request hash not
        being resolved before the Hawk receiver gets the second request.
        """
        try:
            self.perform_authentication(request)
        except DoubleRequestException:
            raise Http404()

        try:
            self.application = get_application(self.kwargs["pk"])
        except (ObjectDoesNotExist, NotFoundError):
            raise Http404()
        return super().initial(request, *args, **kwargs)

    def get_case(self):
        return self.application
