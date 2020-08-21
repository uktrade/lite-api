from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View


class LoginProviderView(View):
    """If user if not logged in then send them to staff sso, otherwise show them vanilla django admin login page"""

    def dispatch(self, request):
        if request.user.is_anonymous:
            return redirect(reverse("authbroker_client:login"))
        # to show the "you're not an admin" message.
        return admin.site.login(request)
