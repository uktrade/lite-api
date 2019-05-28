import reversion
from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView


from applications.models import SitesOnApplication
from applications.libraries.get_application import get_application_by_pk
from applications.serializers import SiteOnApplicationViewSerializer
from conf.authentication import PkAuthentication
from organisations.libraries.get_site import get_site_by_pk
from organisations.serializers import SiteViewSerializer


class ApplicationSites(APIView):
    """
    View sites belonging to an Application or add one
    """
    authentication_classes = (PkAuthentication,)

    def get(self, request, pk):
        application = get_application_by_pk(pk)

        sites_on_application = SitesOnApplication.objects.filter(application=application)
        serializer = SiteViewSerializer(sites_on_application, many=True)
        return JsonResponse(data={'sites': serializer.data},
                            safe=False)

    def post(self, request, pk):
        data = JSONParser().parse(request)

        data['site'] = data['site_id']
        data['application'] = str(pk)

        get_application_by_pk(pk)                       # validate application object
        get_site_by_pk(pk)                              # validate site object

        with reversion.create_revision():
            serializer = SiteOnApplicationViewSerializer(data=data)
            if serializer.is_valid():
                serializer.save()

                reversion.set_user(request.user)
                reversion.set_comment("Created Site on Application Revision")

                return JsonResponse(data={'sites': serializer.data},
                                    status=status.HTTP_201_CREATED)

            return JsonResponse(data={'errors': serializer.errors},
                                status=400)
