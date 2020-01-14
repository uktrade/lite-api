from datetime import datetime

from cases.models import Case
from test_helpers.clients import DataTestClient


class ReferenceCode(DataTestClient):
    def test_standard_application_reference_code(self):
        standard_application = self.create_standard_application(self.organisation)
        self.assertEquals(standard_application.reference_code, "P/GBS??/" + str(datetime.now().year) + "/0000001")

    def test_open_application_reference_code(self):
        open_application = self.create_open_application(self.organisation)
        self.assertEquals(open_application.reference_code, "P/GBO??/" + str(datetime.now().year) + "/0000001")

    def test_hmrc_query_reference_code(self):
        hmrc_query = self.create_hmrc_query(self.organisation)
        self.assertEquals(hmrc_query.reference_code, "CRE/" + str(datetime.now().year) + "/0000001")

    def test_end_user_advisory_reference_code(self):
        end_user_advisory_query = self.create_end_user_advisory_case("", "", self.organisation)
        self.assertEquals(end_user_advisory_query.reference_code, "EUA/" + str(datetime.now().year) + "/0000001")

    def test_control_list_classification_reference_code(self):
        clc_query = self.create_clc_query("", self.organisation)
        self.assertEquals(clc_query.reference_code, "GQY/" + str(datetime.now().year) + "/0000001")
