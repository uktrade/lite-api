from datetime import datetime

from api.applications.enums import ApplicationExportType
from api.cases.enums import CaseTypeEnum
from api.cases.libraries.reference_code import CASE_TYPE_MAP
from test_helpers.clients import DataTestClient

PERMANENT = "P"
TEMPORARY = "T"


def build_expected_reference(case_reference):
    reference_number = "0000001"
    year = str(datetime.now().year)

    return f"{CASE_TYPE_MAP[case_reference]}{year[-2:]}-{reference_number}-01"


class ReferenceCode(DataTestClient):
    def test_standard_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application = self.submit_application(standard_application)

        expected_reference = build_expected_reference(CaseTypeEnum.SIEL.reference)
        self.assertEqual(standard_application.reference_code, expected_reference)

    def test_standard_individual_transhipment_application_reference_code(self):
        standard_application = self.create_draft_standard_application(
            self.organisation, case_type_id=CaseTypeEnum.SITL.id,
        )
        standard_application = self.submit_application(standard_application)

        expected_reference = build_expected_reference(CaseTypeEnum.SITL.reference)
        self.assertEqual(standard_application.reference_code, expected_reference)

    def test_open_application_reference_code(self):
        open_application = self.create_draft_open_application(self.organisation)
        open_application = self.submit_application(open_application)

        expected_reference = build_expected_reference(CaseTypeEnum.OIEL.reference)
        self.assertEqual(open_application.reference_code, expected_reference)

    def test_exhibition_clearance_reference_code(self):
        exhibition_clearance = self.create_mod_clearance_application(
            self.organisation, case_type=CaseTypeEnum.EXHIBITION
        )
        exhibition_clearance = self.submit_application(exhibition_clearance)

        expected_reference = build_expected_reference(CaseTypeEnum.EXHIBITION.reference)
        self.assertEqual(exhibition_clearance.reference_code, expected_reference)

    def test_f680_clearance_reference_code(self):
        f680_clearance = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.F680)
        f680_clearance = self.submit_application(f680_clearance)

        expected_reference = build_expected_reference(CaseTypeEnum.F680.reference)
        self.assertEqual(f680_clearance.reference_code, expected_reference)

    def test_gifting_clearance_reference_code(self):
        gifting_clearance = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.GIFTING)
        gifting_clearance = self.submit_application(gifting_clearance)

        expected_reference = build_expected_reference(CaseTypeEnum.GIFTING.reference)
        self.assertEqual(gifting_clearance.reference_code, expected_reference)

    def test_hmrc_query_reference_code(self):
        hmrc_query = self.create_hmrc_query(self.organisation)
        hmrc_query = self.submit_application(hmrc_query)

        expected_reference = build_expected_reference(CaseTypeEnum.HMRC.reference)
        self.assertEqual(hmrc_query.reference_code, expected_reference)

    def test_end_user_advisory_reference_code(self):
        end_user_advisory_query = self.create_end_user_advisory_case("", "", self.organisation)

        expected_reference = build_expected_reference(CaseTypeEnum.EUA.reference)
        self.assertEqual(end_user_advisory_query.reference_code, expected_reference)

    def test_control_list_classification_reference_code(self):
        clc_query = self.create_clc_query("", self.organisation)

        expected_reference = build_expected_reference(CaseTypeEnum.GOODS.reference)
        self.assertEqual(clc_query.reference_code, expected_reference)

    def test_temporary_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application.export_type = ApplicationExportType.TEMPORARY
        self.submit_application(standard_application)

        expected_reference = build_expected_reference(CaseTypeEnum.SIEL.reference)
        self.assertEqual(standard_application.reference_code, expected_reference)

    def test_trade_control_application_reference_code(self):
        standard_application = self.create_draft_standard_application(
            self.organisation, case_type_id=CaseTypeEnum.SICL.id
        )
        standard_application = self.submit_application(standard_application)

        expected_reference = build_expected_reference(CaseTypeEnum.SICL.reference)
        self.assertEqual(standard_application.reference_code, expected_reference)

    def test_draft_applications_dont_have_reference_codes(self):
        draft = self.create_draft_standard_application(self.organisation)

        self.assertIsNone(draft.reference_code)

    def test_reference_code_increment(self):
        case_1 = self.create_clc_query("", self.organisation)
        case_2 = self.create_clc_query("", self.organisation)

        self.assertIn("1", case_1.reference_code)
        self.assertIn("2", case_2.reference_code)
