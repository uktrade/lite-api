from django.urls import reverse

from applications.models import StandardApplication, BaseApplication
from test_helpers.clients import DataTestClient


def _create_copy_of_object(obj):
    model = type(obj)
    obj = model.objects.get(pk=obj.pk)
    obj.pk = None
    obj.id = None
    obj.save()

    return obj


def _create_copy_of_objects(objs):
    return [_create_copy_of_object(obj) for obj in objs]


def _copy_standard_application(application_to_copy: StandardApplication):
    copied_standard_application = _create_copy_of_object(application_to_copy)
    copied_standard_application.third_parties.set(application_to_copy.third_parties.all())

    application_to_copy.application_copied_to = copied_standard_application
    application_to_copy.save()

    return copied_standard_application


class StandardApplicationEditTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.draft = self.create_standard_draft(self.organisation)
        self.url = reverse('applications:application_submit', kwargs={'pk': self.draft.id})

    def test_initial_edit_of_standard_application(self):
        """
        This tests the functionality of the initial step of editing an application.
        This will happen when we hit the "edit" button;
        A shallow copy of the application will be created and a pointer to this copy will be placed on the original
        application (see model).

        This pointer can be used as a switch statement when retrieving an individual application i.e.:
            if application.application_copied_to is not None:
                return StandardApplication.objects.get(pk=application.application_copied_to)


        ------------------------------------------------------------------------------------------------------------

        When we update the parties/goods etc. on the copied application (the instance being edited),
        DO NOT DELETE THE PREVIOUSLY SET PARTY/GOOD IF IT'S THE SAME AS THE ONE ON THE ORIGINAL APPLICATION (THE
        APPLICATION WE COPIED FROM)

        If we click "save", iterate through all of the original application's items deleting the ones which are not
        equal to the edited application's items. Then delete the original application. Then set the edited version of
        the application's pk to equal the original application's pk.

        If we click "cancel", iterate through all of the copied application's items and delete the ones which are not
        equal to the original application's items. Then reset the `application_copied_to` field to None.
        """

        application = self.create_standard_application(self.organisation)
        copied_standard_application = _copy_standard_application(application)

        self.assertEqual(BaseApplication.objects.filter(submitted_at__isnull=False).count(), 2)
        self.assertEqual(copied_standard_application.pk, application.application_copied_to.pk)
        self.assertNotEqual(copied_standard_application.pk, application.pk)

        self.assertEqual(copied_standard_application.activity, application.activity)
        self.assertEqual(copied_standard_application.usage, application.usage)
        self.assertEqual(copied_standard_application.licence_type, application.licence_type)
        self.assertEqual(copied_standard_application.export_type, application.export_type)
        self.assertEqual(copied_standard_application.reference_number_on_information_form,
                         application.reference_number_on_information_form)
        self.assertEqual(copied_standard_application.have_you_been_informed, application.have_you_been_informed)
        self.assertEqual(copied_standard_application.organisation, application.organisation)
        self.assertEqual(copied_standard_application.status, application.status)
        self.assertEqual(copied_standard_application.created_at, application.created_at)
        self.assertEqual(copied_standard_application.last_modified_at, application.last_modified_at)
        self.assertEqual(copied_standard_application.submitted_at, application.submitted_at)
        self.assertEqual(copied_standard_application.end_user, application.end_user)
        self.assertEqual(copied_standard_application.consignee, application.consignee)
        self.assertEqual(set(copied_standard_application.third_parties.all()), set(application.third_parties.all()))
