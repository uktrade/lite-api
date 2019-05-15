from rest_framework.views import APIView

from organisations.libraries.get_organisation import get_organisation_by_user


class ApplicationSites(APIView):
    """
    View sites belonging to an Application or add one
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        organisation = get_organisation_by_user(request.user)
        application =


