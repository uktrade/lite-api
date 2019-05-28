from django.test import TestCase

from applications.models import Application, ExportType, LicenceType
from cases.models import Case
from queues.models import Queue


class QueueModelTests(TestCase):

    def test_queue_model(self):
        """
        Tests the Queue model has been created correctly
        """
        new_application = Application(name='Test',
                                      activity='Trade',
                                      status='',
                                      licence_type=LicenceType.open_licence,
                                      export_type=ExportType.permanent,
                                      reference_number_on_information_form='',
                                      usage='Fun')
        new_application.save()
        new_case = Case(application=new_application)
        new_case.save()
        new_queue = Queue(name='New_Queue')
        new_queue.save()
        new_queue.cases.add(new_case)
        q_set = Queue.objects.get(name='New_Queue')
        q_set_case = Queue.objects.filter(cases__id=new_case.id)
        q_set_case_app = Queue.objects.filter(cases__application__name='Test')

        self.assertEqual(q_set.name, 'New_Queue')
        self.assertEqual(q_set_case.count(), 1)
        self.assertEqual(q_set_case_app.count(), 1)
