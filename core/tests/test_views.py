from django.test import override_settings, TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model

User = get_user_model()


class FlagsUpdateTest(TestCase):
    def test_login_anonymous_user(self):
        # when an anonymous user accesses login
        response = self.client.get(reverse("admin:login"))
        # then they are sent to the staff sso login
        self.assertRedirects(response, reverse("authbroker_client:login"), fetch_redirect_response=False)

    @override_settings(ALLOWED_ADMIN_EMAILS=[])
    def test_login_authenticated_user_permission_denied(self):
        # given the logged in user does not have permission to admin
        user = User.objects.create(email="test@example.com")
        self.client.force_login(user)

        # when the user accesses admin
        response = self.client.get(reverse("admin:login"))

        # then they are not shown admin
        self.assertContains(response, "not authorized to access this page", status_code=200)

    @override_settings(ALLOWED_ADMIN_EMAILS=["test@example.com"])
    def test_login_authenticated_user_permission_granted(self):
        # given the logged in user has permission to admin
        user = User.objects.create(email="test@example.com")
        self.client.force_login(user)

        # when the user accesses admin
        response = self.client.get(reverse("admin:index"))

        # then they are shown admin
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/index.html")
