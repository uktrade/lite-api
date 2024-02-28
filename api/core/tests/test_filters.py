import uuid

from django.core.exceptions import ImproperlyConfigured
from django.test import (
    override_settings,
    SimpleTestCase,
    TestCase,
)
from django.urls import reverse

from api.core.tests.models import (
    ChildModel,
    ParentModel,
)


@override_settings(
    ROOT_URLCONF="api.core.tests.urls",
)
class TestMisconfiguredParentFilter(SimpleTestCase):
    def test_misconfigured_parent_filter(self):
        url = reverse(
            "test-misconfigured-parent-filter",
            kwargs={
                "pk": str(uuid.uuid4()),
                "child_pk": str(uuid.uuid4()),
            },
        )
        with self.assertRaises(ImproperlyConfigured):
            self.client.get(url)


@override_settings(
    ROOT_URLCONF="api.core.tests.urls",
)
class TestParentFilter(TestCase):
    def test_parent_filter(self):
        parent = ParentModel.objects.create(name="parent")
        child = ChildModel.objects.create(parent=parent, name="child")
        url = reverse(
            "test-parent-filter",
            kwargs={
                "pk": str(parent.pk),
                "child_pk": str(child.pk),
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_parent_other_parent_filter(self):
        parent = ParentModel.objects.create(name="parent")
        child = ChildModel.objects.create(parent=parent, name="child")
        other_parent = ParentModel.objects.create(name="other_parent")
        url = reverse(
            "test-parent-filter",
            kwargs={
                "pk": str(other_parent.pk),
                "child_pk": str(child.pk),
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
