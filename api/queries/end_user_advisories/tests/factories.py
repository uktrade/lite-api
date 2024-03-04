import factory
from api.queries.end_user_advisories.models import EndUserAdvisoryQuery
from api.cases.tests.factories import CaseFactory


class EndUserAdvisoryQueryFactory(CaseFactory):
    end_user = factory.SubFactory("api.parties.tests.factories.PartyFactory")

    class Meta:
        model = EndUserAdvisoryQuery
