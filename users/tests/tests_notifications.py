from applications.models import Application
from test_helpers.clients import DataTestClient
from test_helpers.org_and_user_helper import OrgAndUserHelper
from users.models import Notification
from django.urls import reverse


class NotificationTests(DataTestClient):

    def tests_create_new_clc_query_notification(self):

        clc_case = self.create_clc_query_case("Case Ref")

        self.create_case_note_visible_to_exporter(clc_case, "This is a test note 1")
        self.create_case_note_visible_to_exporter(clc_case, "This is a test note 2")
        self.create_case_note_visible_to_exporter(clc_case, "This is a test note 3")
        self.create_case_note(clc_case, "This is a test note 4")

        self.assertEqual(Notification.objects.all().count(), 3)

    # def tests_create_new_application_notification(self):
    #     draft = self.test_helper.create_draft_with_good_end_user_and_site('Example Application',
    #                                                                           self.test_helper.organisation)
    #     application = self.test_helper.submit_draft(self, draft)
    #     self.url = reverse('applications:application', kwargs={'pk': application.id})


        # app_case = Case.objects.get(application=application)
        # self.create_case_note(app_case, "This is a test note 1")
        # self.create_case_note_visible_to_exporter(app_case, "This is a test note 2")
        # self.assertEqual(Notification.objects.all().count(), 1)



    # def tests_create_both_clc_and_application_notifications(self):
    #
    #     app_case = self.create_application_case("Case Ref")
    #     clc_case = self.create_clc_query_case("Case Ref")
    #
    #     self.create_case_note_visible_to_exporter(app_case, "This is a test note 1")
    #     self.create_case_note_visible_to_exporter(app_case, "This is a test note 2")
    #     self.create_case_note_visible_to_exporter(app_case, "This is a test note 3")
    #     self.create_case_note_visible_to_exporter(app_case, "This is a test note 4")
    #
    #     self.create_case_note_visible_to_exporter(clc_case, "This is a test note 1")
    #     self.create_case_note_visible_to_exporter(clc_case, "This is a test note 2")
    #     self.create_case_note_visible_to_exporter(clc_case, "This is a test note 3")
    #
    #     self.assertEqual(Notification.objects.all().count(), 7)
    #     self.assertEqual(Notification.objects.filter(note__case__clc_query_id__isnull=True).count(), 4)
    #     self.assertEqual(Notification.objects.filter(note__case__application_id__isnull=True).count(), 3)

