from datetime import datetime

from applications.enums import ApplicationExportType
from applications.models import ExternalLocationOnApplication
from cases.enums import CaseTypeEnum
from cases.libraries.reference_code import (
    APPLICATION_PREFIX,
    STANDARD,
    OPEN,
    INDIVIDUAL,
    EXPORT,
    SEPARATOR,
    PERMANENT,
    EXHIBITION_CLEARANCE_PREFIX,
    F680_CLEARANCE_PREFIX,
    GIFTING_CLEARANCE_PREFIX,
    HMRC_PREFIX,
    END_USER_ADVISORY_QUERY_PREFIX,
    GOODS_QUERY_PREFIX,
    TEMPORARY,
    TRADE_CONTROL,
    LICENCE,
    TRANSHIPMENT,
)
from test_helpers.clients import DataTestClient


class ReferenceCode(DataTestClient):
    def test_standard_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application = self.submit_application(standard_application)

        expected_prefix = APPLICATION_PREFIX + STANDARD + INDIVIDUAL + EXPORT + LICENCE + SEPARATOR
        expected_postfix = SEPARATOR + "0000001" + SEPARATOR + PERMANENT
        self.assertEquals(
            standard_application.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_standard_individual_transhipment_application_reference_code(self):
        standard_application = self.create_draft_standard_application(
            self.organisation, case_type_id=CaseTypeEnum.SITL.id,
        )
        standard_application = self.submit_application(standard_application)

        expected_prefix = APPLICATION_PREFIX + STANDARD + INDIVIDUAL + TRANSHIPMENT + LICENCE + SEPARATOR
        expected_postfix = SEPARATOR + "0000001" + SEPARATOR + PERMANENT
        self.assertEquals(
            standard_application.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_open_application_reference_code(self):
        open_application = self.create_draft_open_application(self.organisation)
        open_application = self.submit_application(open_application)

        expected_prefix = APPLICATION_PREFIX + OPEN + INDIVIDUAL + EXPORT + LICENCE + SEPARATOR
        expected_postfix = SEPARATOR + "0000001" + SEPARATOR + PERMANENT
        self.assertEquals(
            open_application.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_exhibition_clearance_reference_code(self):
        exhibition_clearance = self.create_mod_clearance_application(
            self.organisation, case_type=CaseTypeEnum.EXHIBITION
        )
        exhibition_clearance = self.submit_application(exhibition_clearance)

        expected_prefix = EXHIBITION_CLEARANCE_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(
            exhibition_clearance.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_f680_clearance_reference_code(self):
        exhibition_clearance = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.F680)
        exhibition_clearance = self.submit_application(exhibition_clearance)

        expected_prefix = F680_CLEARANCE_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(
            exhibition_clearance.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_gifting_clearance_reference_code(self):
        exhibition_clearance = self.create_mod_clearance_application(self.organisation, case_type=CaseTypeEnum.GIFTING)
        exhibition_clearance = self.submit_application(exhibition_clearance)

        expected_prefix = GIFTING_CLEARANCE_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(
            exhibition_clearance.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_hmrc_query_reference_code(self):
        hmrc_query = self.create_hmrc_query(self.organisation)
        hmrc_query = self.submit_application(hmrc_query)

        expected_prefix = HMRC_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(hmrc_query.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix)

    def test_end_user_advisory_reference_code(self):
        end_user_advisory_query = self.create_end_user_advisory_case("", "", self.organisation)

        expected_prefix = END_USER_ADVISORY_QUERY_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(
            end_user_advisory_query.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_control_list_classification_reference_code(self):
        clc_query = self.create_clc_query("", self.organisation)

        expected_prefix = GOODS_QUERY_PREFIX + SEPARATOR
        expected_postfix = SEPARATOR + "0000001"
        self.assertEquals(clc_query.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix)

    def test_temporary_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application.export_type = ApplicationExportType.TEMPORARY
        self.submit_application(standard_application)

        expected_prefix = APPLICATION_PREFIX + STANDARD + INDIVIDUAL + EXPORT + LICENCE + SEPARATOR
        expected_postfix = SEPARATOR + "0000001" + SEPARATOR + TEMPORARY
        self.assertEquals(
            standard_application.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_trade_control_application_reference_code(self):
        standard_application = self.create_draft_standard_application(self.organisation)
        standard_application.application_sites.all().delete()
        external_location = self.create_external_location("storage facility", self.organisation)
        external_location_on_app = ExternalLocationOnApplication(
            application=standard_application, external_location=external_location
        )
        external_location_on_app.save()
        standard_application.external_application_sites.set([external_location_on_app])
        standard_application = self.submit_application(standard_application)

        expected_prefix = APPLICATION_PREFIX + STANDARD + INDIVIDUAL + TRADE_CONTROL + LICENCE + SEPARATOR
        expected_postfix = SEPARATOR + "0000001" + SEPARATOR + PERMANENT
        self.assertEquals(
            standard_application.reference_code, expected_prefix + str(datetime.now().year) + expected_postfix
        )

    def test_draft_applications_dont_have_reference_codes(self):
        draft = self.create_draft_standard_application(self.organisation)

        self.assertIsNone(draft.reference_code)

    def test_reference_code_increment(self):
        case_1 = self.create_clc_query("", self.organisation)
        case_2 = self.create_clc_query("", self.organisation)

        self.assertIn("1", case_1.reference_code)
        self.assertIn("2", case_2.reference_code)
