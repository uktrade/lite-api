from cases.models import Case, Notification
from test_helpers.clients import DataTestClient


class NotificationTests(DataTestClient):

    def test_create_new_clc_query_notification(self):

        clc_case = self.create_clc_query('Example CLC Query', self.organisation).case.get()

        self.create_case_note(clc_case, 'This is a test note 1', self.gov_user, True)
        self.create_case_note(clc_case, 'This is a test note 2', self.gov_user, True)
        self.create_case_note(clc_case, 'This is a test note 3', self.gov_user, True)
        self.create_case_note(clc_case, 'This is a test note 4', self.gov_user, False)

        self.assertEqual(Notification.objects.all().count(), 3)

    def test_create_new_application_notification(self):
        application = self.create_standard_application(self.organisation)
        case = Case.objects.get(application=application)

        self.create_case_note(case, 'This is a test note 1', self.gov_user, True)
        self.create_case_note(case, 'This is a test note 2', self.gov_user, False)

        self.assertEqual(Notification.objects.all().count(), 1)

    def test_create_both_clc_and_application_notifications(self):
        application = self.create_standard_application(self.organisation)
        case = Case.objects.get(application=application)

        clc_case = self.create_clc_query('Example CLC Query', self.organisation).case.get()

        self.create_case_note(case, 'This is a test note 1', self.gov_user, True)
        self.create_case_note(case, 'This is a test note 2', self.gov_user, True)
        self.create_case_note(case, 'This is a test note 3', self.gov_user, True)
        self.create_case_note(case, 'This is a test note 4', self.gov_user, True)

        self.create_case_note(clc_case, 'This is a test note 1', self.gov_user, True)
        self.create_case_note(clc_case, 'This is a test note 2', self.gov_user, True)
        self.create_case_note(clc_case, 'This is a test note 3', self.gov_user, True)

        self.assertEqual(Notification.objects.all().count(), 7)
        self.assertEqual(Notification.objects.filter(case_note__case__query_id__isnull=True).count(), 4)
        self.assertEqual(Notification.objects.filter(case_note__case__application_id__isnull=True).count(), 3)
