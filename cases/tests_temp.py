from django.test import tag

from cases.libraries.activity_types import CaseActivityType
from cases.models import CaseActivity
from test_helpers.clients import DataTestClient


class CaseActivityTests(DataTestClient):

    @tag('only')
    def test_test(self):
        case = self.create_clc_query('', self.organisation).case.get()

        activity = CaseActivity.create(activity_type=CaseActivityType.ADD_FLAGS,
                                       case=case,
                                       user=self.gov_user,
                                       flags=['banana', 'potato', 'hairpin turns'])

        CaseActivity.create(activity_type=CaseActivityType.MOVE_QUEUE,
                            case=case,
                            user=self.gov_user,
                            case_name='Rylan',
                            queue='Get Some Sun')

        print(activity.__dict__)
        print(activity.text)
