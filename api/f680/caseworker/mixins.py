from api.core.authentication import GovAuthentication
from api.f680.caseworker import filters


class F680CaseworkerApplicationMixin:
    authentication_classes = (GovAuthentication,)
    filter_backends = (filters.F680CaseFilter, filters.CurrentCaseFilter)

    # def initial(self, request, *args, **kwargs):
    #     """
    #     Below we are catching a situation where there is a post request inside of which auth
    #     is performed and therefore we get a hawk exception due to the first post request hash not
    #     being resolved before the Hawk receiver gets the second request.
    #     """
    #     super().initial(request, *args, **kwargs)

    #     try:
    #         self.application = get_application(self.kwargs["pk"])
    #     except (ObjectDoesNotExist, NotFoundError):
    #         raise Http404()
