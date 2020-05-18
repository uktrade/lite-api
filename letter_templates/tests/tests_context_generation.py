from audit_trail.models import Audit
from cases.enums import AdviceLevel, AdviceType
from conf.helpers import add_months, DATE_FORMAT
from letter_templates.context_generator import get_document_context
from parties.enums import PartyType
from static.countries.models import Country
from test_helpers.clients import DataTestClient


class DocumentContextGenerationTests(DataTestClient):
    def _assert_applicant(self, context, case):
        applicant = Audit.objects.filter(target_object_id=case.id).first().actor
        self.assertEqual(context["name"], " ".join([applicant.first_name, applicant.last_name]))
        self.assertEqual(context["email"], applicant.email)

    def _assert_organisation(self, context, organisation):
        self.assertEqual(context["name"], organisation.name)
        self.assertEqual(context["eori_number"], organisation.eori_number)
        self.assertEqual(context["sic_number"], organisation.sic_number)
        self.assertEqual(context["vat_number"], organisation.vat_number)
        self.assertEqual(context["registration_number"], organisation.registration_number)
        self.assertEqual(context["primary_site"]["name"], organisation.primary_site.name)
        self.assertEqual(
            context["primary_site"]["address_line_1"],
            organisation.primary_site.address.address_line_1 or organisation.primary_site.address.address,
        )
        self.assertEqual(context["primary_site"]["address_line_2"], organisation.primary_site.address.address_line_2)
        self.assertEqual(context["primary_site"]["postcode"], organisation.primary_site.address.postcode)
        self.assertEqual(context["primary_site"]["city"], organisation.primary_site.address.city)
        self.assertEqual(context["primary_site"]["region"], organisation.primary_site.address.region)
        self.assertEqual(context["primary_site"]["country"]["name"], organisation.primary_site.address.country.name)
        self.assertEqual(context["primary_site"]["country"]["code"], organisation.primary_site.address.country.id)

    def _assert_licence(self, context, licence):
        self.assertEqual(context["start_date"], licence.start_date.strftime(DATE_FORMAT))
        self.assertEqual(context["duration"], licence.duration)
        self.assertEqual(context["end_date"], add_months(licence.start_date, licence.duration))

    def _assert_party(self, context, party):
        self.assertEqual(context["name"], party.name)
        self.assertEqual(context["address"], party.address)
        self.assertEqual(context["country"]["name"], party.country.name)
        self.assertEqual(context["country"]["code"], party.country.id)
        self.assertEqual(context["website"], party.website)

    def _assert_third_party(self, context, third_party):
        self.assertEqual(len(context["all"]), 1)
        self._assert_party(context["all"][0], third_party)
        self.assertEqual(len(context[third_party.role]), 1)
        self._assert_party(context[third_party.role][0], third_party)

    def _assert_good(self, context, good_on_application):
        self.assertEqual(context["description"], good_on_application.good.description)
        self.assertEqual(
            context["control_list_entries"],
            [clc.rating for clc in good_on_application.good.control_list_entries.all()],
        )

    def _assert_good_with_advice(self, context, advice, good_on_application):
        goods = context[advice.type if advice.type != AdviceType.PROVISO else AdviceType.APPROVE]
        self.assertEqual(len(goods), 1)
        self._assert_good(goods[0], good_on_application)
        self.assertEqual(goods[0]["reason"], advice.text)
        self.assertEqual(goods[0]["note"], advice.note)

    def _assert_goods_type(self, context, country, goods_type):
        goods_types = context[country.name]
        self.assertEqual(len(goods_types), 1)
        self.assertEqual(goods_types[0]["description"], goods_type.description)
        self.assertEqual(
            goods_types[0]["control_list_entries"], [clc.rating for clc in goods_type.control_list_entries.all()],
        )

    def _assert_ecju_query(self, context, ecju_query):
        self.assertEqual(context["question"]["text"], ecju_query.question)
        self.assertEqual(
            context["question"]["user"],
            " ".join([ecju_query.raised_by_user.first_name, ecju_query.raised_by_user.last_name]),
        )
        self.assertIsNotNone(context["question"]["date"])
        self.assertIsNotNone(context["question"]["time"])
        self.assertEqual(context["response"]["text"], ecju_query.response)
        self.assertEqual(
            context["response"]["user"],
            " ".join([ecju_query.responded_by_user.first_name, ecju_query.responded_by_user.last_name]),
        )
        self.assertIsNotNone(context["response"]["date"])
        self.assertIsNotNone(context["response"]["time"])

    def _assert_note(self, context, note):
        self.assertEqual(context["text"], note.text)
        self.assertEqual(
            context["user"], " ".join([note.user.first_name, note.user.last_name]),
        )
        self.assertIsNotNone(context["date"])
        self.assertIsNotNone(context["time"])

    def test_generate_context_with_parties(self):
        # Standard application with all party types
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        self.create_party("Ultimate end user", self.organisation, PartyType.ULTIMATE_END_USER, case)

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self.assertIsNotNone(context["date"])
        self.assertIsNotNone(context["time"])
        self._assert_applicant(context["applicant"], case)
        self._assert_organisation(context["organisation"], self.organisation)
        self._assert_party(context["end_user"], case.end_user.party)
        self._assert_party(context["consignee"], case.consignee.party)
        self.assertEqual(len(context["ultimate_end_users"]), 1)
        self._assert_party(context["ultimate_end_users"][0], case.ultimate_end_users[0].party)
        # Third party should be in "all" list and role specific list
        self.assertEqual(len(context["third_parties"]), 2)
        self._assert_third_party(context["third_parties"], case.third_parties[0].party)

    def test_generate_context_with_goods(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self._assert_good(context["goods"]["all"][0], case.goods.all()[0])

    def test_generate_context_with_advice_on_goods(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        final_advice = self.create_advice(
            self.gov_user, case, "good", AdviceType.APPROVE, AdviceLevel.FINAL, advice_text="abc",
        )

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])

    def test_generate_context_with_proviso_advice_on_goods(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        final_advice = self.create_advice(
            self.gov_user, case, "good", AdviceType.PROVISO, AdviceLevel.FINAL, advice_text="abc",
        )

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self._assert_good_with_advice(context["goods"], final_advice, case.goods.all()[0])
        self.assertEqual(context["goods"][AdviceType.APPROVE][0]["proviso_reason"], final_advice.proviso)

    def test_generate_context_with_goods_types(self):
        case = self.create_open_application_case(self.organisation)
        case.goods_type.first().countries.set([Country.objects.first()])
        case.goods_type.last().countries.set([Country.objects.last()])

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self._assert_goods_type(context["goods_type"], Country.objects.first(), case.goods_type.first())
        self._assert_goods_type(context["goods_type"], Country.objects.last(), case.goods_type.last())

    def test_generate_context_with_licence(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        licence = self.create_licence(case, is_complete=True)

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self._assert_licence(context["licence"], licence)

    def test_generate_context_with_application_details(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)

        context = get_document_context(case)

        self.assertEqual(context["reference"], case.reference_code)
        self.assertEqual(context["details"]["end_use_details"], case.baseapplication.intended_end_use)

    def test_generate_context_with_ecju_query(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        ecju_query = self.create_ecju_query(case)
        ecju_query.response = "abc"
        ecju_query.responded_by_user = self.exporter_user
        ecju_query.save()

        context = get_document_context(case)
        self.assertEqual(context["reference"], case.reference_code)
        self._assert_ecju_query(context["ecju_queries"][0], ecju_query)

    def test_generate_context_with_case_note(self):
        case = self.create_standard_application_case(self.organisation, user=self.exporter_user)
        note = self.create_case_note(case, "text", self.gov_user)

        context = get_document_context(case)
        self.assertEqual(context["reference"], case.reference_code)
        self._assert_note(context["notes"][0], note)
