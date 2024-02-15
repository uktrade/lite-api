from django.contrib import admin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View

from rest_framework.generics import RetrieveAPIView

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
