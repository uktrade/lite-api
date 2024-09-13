from django.test import TestCase

from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.support.helpers import developer_intervention
from api.support.tests.models import FakeModel
from api.users.enums import SystemUser
from api.users.models import BaseUser


class DeveloperInterventionTests(TestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.system_user = BaseUser.objects.get(id=SystemUser.id)

    def test_dry_run_makes_no_changes(self):
        self.assertEqual(Audit.objects.count(), 0)

        fake_model = FakeModel.objects.create(thing="testing")
        with developer_intervention() as audit_log:
            fake_model.thing = "something else"
            fake_model.save()
            audit_log(fake_model, "Changed the model")

        fake_model.refresh_from_db()
        self.assertEqual(fake_model.thing, "testing")
        self.assertEqual(Audit.objects.count(), 0)

    def test_calling_without_logging_errors(self):
        self.assertEqual(Audit.objects.count(), 0)

        fake_model = FakeModel.objects.create(thing="testing")
        with self.assertRaises(ValueError):
            with developer_intervention(dry_run=False):
                fake_model.thing = "something else"
                fake_model.save()

        fake_model.refresh_from_db()
        self.assertEqual(fake_model.thing, "testing")
        self.assertEqual(Audit.objects.count(), 0)

    def test_changes_saved(self):
        self.assertEqual(Audit.objects.count(), 0)

        fake_model = FakeModel.objects.create(thing="testing")
        with developer_intervention(dry_run=False) as audit_log:
            fake_model.thing = "something else"
            fake_model.save()
            audit_log(fake_model, "Changed the model")

        fake_model.refresh_from_db()
        self.assertEqual(fake_model.thing, "something else")
        self.assertEqual(Audit.objects.count(), 1)
        audit = Audit.objects.get()
        self.assertEqual(audit.target, fake_model)
        self.assertEqual(audit.payload, {"additional_text": "Changed the model"})
        self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
        self.assertEqual(audit.actor, self.system_user)

    def test_multiple_log_entries(self):
        self.assertEqual(Audit.objects.count(), 0)

        fake_model = FakeModel.objects.create(thing="testing")
        another_fake_model = FakeModel.objects.create(thing="another")
        with developer_intervention(dry_run=False) as audit_log:
            fake_model.thing = "something else"
            fake_model.save()
            audit_log(fake_model, "Changed the first model")

            another_fake_model.thing = "another something else"
            another_fake_model.save()
            audit_log(another_fake_model, "Changed the second model")

        fake_model.refresh_from_db()
        self.assertEqual(fake_model.thing, "something else")

        another_fake_model.refresh_from_db()
        self.assertEqual(another_fake_model.thing, "another something else")

        self.assertEqual(Audit.objects.count(), 2)
        audit = Audit.objects.order_by("created_at")[0]
        self.assertEqual(audit.target, fake_model)
        self.assertEqual(audit.payload, {"additional_text": "Changed the first model"})
        self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
        self.assertEqual(audit.actor, self.system_user)

        audit = Audit.objects.order_by("created_at")[1]
        self.assertEqual(audit.target, another_fake_model)
        self.assertEqual(audit.payload, {"additional_text": "Changed the second model"})
        self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
        self.assertEqual(audit.actor, self.system_user)

    def test_additional_kwargs(self):
        self.assertEqual(Audit.objects.count(), 0)

        fake_model = FakeModel.objects.create(thing="testing")
        with developer_intervention(dry_run=False) as audit_log:
            fake_model.thing = "something else"
            fake_model.save()
            audit_log(
                fake_model,
                "Changed the model",
                additional_payload={"something_else": "this is something else"},
            )

        fake_model.refresh_from_db()
        self.assertEqual(fake_model.thing, "something else")
        self.assertEqual(Audit.objects.count(), 1)
        audit = Audit.objects.get()
        self.assertEqual(audit.target, fake_model)
        self.assertEqual(
            audit.payload,
            {
                "additional_text": "Changed the model",
                "something_else": "this is something else",
            },
        )
        self.assertEqual(audit.verb, AuditType.DEVELOPER_INTERVENTION)
        self.assertEqual(audit.actor, self.system_user)
