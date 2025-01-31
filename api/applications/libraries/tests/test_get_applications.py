import pytest
from uuid import uuid4

from api.applications.libraries.get_applications import get_application
from api.cases.models import Case
from api.applications.tests.factories import StandardApplicationFactory
from api.organisations.tests.factories import OrganisationFactory

pytestmark = pytest.mark.django_db


class TestGetApplication:

    def test_get_application_no_matching_case(self):
        with pytest.raises(Case.DoesNotExist):
            get_application(uuid4())

    def test_get_application_success(self):
        standard_application = StandardApplicationFactory()
        assert get_application(standard_application.id) == standard_application

    def test_get_application_with_organisation_success(self):
        standard_application = StandardApplicationFactory()
        assert (
            get_application(standard_application.id, organisation_id=standard_application.organisation_id)
            == standard_application
        )

    def test_get_application_with_differing_organisation(self):
        standard_application = StandardApplicationFactory()
        differing_organisation = OrganisationFactory()
        with pytest.raises(Case.DoesNotExist):
            get_application(standard_application.id, organisation_id=differing_organisation.id)
