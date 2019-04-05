from django.test import TestCase

from applications.models import Application
from cases.models import Case
from queues.models import Queue


class QueueModelTests(TestCase):

    def test_queue_model(self):
        """
            Tests the Queue model has been created correctly

        """
        draft_id = '90D6C724-0339-425A-99D2-9D2B8E864EC7'
        new_application = Application(id=draft_id,
                                     user_id='12345',
                                     control_code='ML2',
                                     name='Test',
                                     destination='Poland',
                                     activity='Trade',
                                     usage='Fun',
                                     draft=False)
        new_application.save()
        q_application = Application.objects.get(pk='90D6C724-0339-425A-99D2-9D2B8E864EC7')
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
