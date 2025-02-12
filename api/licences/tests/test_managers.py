from api.licences.tests.factories import StandardLicenceFactory
from api.applications.tests.factories import StandardApplicationFactory
from api.licences.models import Licence
from api.licences.enums import LicenceStatus
from test_helpers.clients import DataTestClient


class LicenceTests(DataTestClient):
    def test_manager_filter_non_draft_licences(self):
        application = StandardApplicationFactory()
        case = application.case_ptr
        StandardLicenceFactory(status=LicenceStatus.DRAFT, case=case)
        issued_licence = StandardLicenceFactory(status=LicenceStatus.ISSUED, case=case)
        cancelled_licence = StandardLicenceFactory(status=LicenceStatus.CANCELLED, case=case)
        assert list(Licence.objects.filter_non_draft_licences(application=application).order_by("reference_code")) == [
            issued_licence,
            cancelled_licence,
        ]
