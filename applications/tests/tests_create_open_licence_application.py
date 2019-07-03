from django.urls import reverse
from rest_framework import status

from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.models import Application
from drafts.models import Draft, SiteOnDraft
from queues.models import Queue
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper


class ApplicationsTests(DataTestClient):

    def setUp(self):
        super().setUp()

    url = reverse('applications:applications')

    def test_create_application_case_and_addition_to_queue(self):
        """
        Test whether we can create a open licence application
        """
        draft = Draft(name='bloggs',
                      licence_type=ApplicationLicenceType.OPEN_LICENCE,
                      export_type=ApplicationExportType.PERMANENT,
                      have_you_been_informed=ApplicationExportLicenceOfficialType.NO,
                      reference_number_on_information_form='',
                      activity='Trade',
                      usage='Fun',
                      organisation=self.test_helper.organisation)
        draft.save()

        draft = OrgAndUserHelper.complete_draft('bloggs', self.test_helper.organisation)

        draft.end_user = OrgAndUserHelper.create_end_user('test', self.test_helper.organisation)
        SiteOnDraft(site=self.test_helper.organisation.primary_site, draft=draft).save()
        draft.save()

        draft = OrgAndUserHelper.create_draft_with_good_end_user_and_site(name='test',
                                                                          org=self.test_helper.organisation)
        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 0)

        data = {'id': draft.id}
        response = self.client.post(self.url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        application = Application.objects.get(pk=draft.id)

        self.assertEqual(Queue.objects.get(pk='00000000-0000-0000-0000-000000000001').cases.count(), 1)
        self.assertEqual(application.end_user, draft.end_user)
