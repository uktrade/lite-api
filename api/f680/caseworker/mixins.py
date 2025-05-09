from api.cases.libraries.get_case import get_case
from api.core.authentication import GovAuthentication
from api.f680.caseworker import filters


class F680CaseworkerApplicationMixin:
    authentication_classes = (GovAuthentication,)
    filter_backends = (filters.F680CaseFilter,)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.case = get_case(self.kwargs["pk"])
