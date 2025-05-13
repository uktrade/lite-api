from django.contrib import admin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View
from api.core.authentication import HawkOnlyAuthentication

from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from waffle import get_waffle_flag_model

from api.documents.libraries.s3_operations import document_download_stream


class LoginProviderView(View):
    """If user if not logged in then send them to staff sso, otherwise show them vanilla django admin login page"""

    def dispatch(self, request):
        if request.user.is_anonymous:
            return redirect(reverse("authbroker_client:login"))
        # to show the "you're not an admin" message.
        return admin.site.login(request)


class DocumentStreamAPIView(RetrieveAPIView):
    def get_document(self, instance):
        raise NotImplementedError()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        document = self.get_document(instance)
        if not document.safe:
            raise Http404()
        return document_download_stream(document)


class FeatureFlagAPIView(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request, *args, **kwargs):
        """
        Return True if the Flag is on otherwise False
        """
        flag_name = self.kwargs["flag_name"]
        if self.flag_is_active(request, flag_name):
            print("flag active api view")
            return Response({"active": True})
        else:
            print("flag not active api view")
            return Response({"active": False})

    def flag_is_active(self, request, flag_name: str, read_only: bool = False):
        """Overriding the flag_is_active class that comes with django-waffle to hit the database and prevent stale in memory flags being used."""
        flag = get_waffle_flag_model().objects.all().get(name=flag_name)
        return flag.is_active(request, read_only=read_only)
