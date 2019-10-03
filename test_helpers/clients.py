from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase, APIClient

from addresses.models import Address
from applications.enums import ApplicationLicenceType, ApplicationExportType, ApplicationExportLicenceOfficialType
from applications.models import Application, GoodOnApplication
from cases.enums import CaseType, AdviceType
from cases.models import CaseNote, Case, CaseDocument, CaseAssignment, GoodCountryDecision
from conf import settings
from conf.urls import urlpatterns
from drafts.models import Draft, GoodOnDraft, SiteOnDraft, CountryOnDraft
from flags.models import Flag
from goods.enums import GoodControlled
from goods.models import Good, GoodDocument
from goodstype.models import GoodsType
from organisations.models import Organisation, Site, ExternalLocation
from parties.document.models import PartyDocument
from parties.enums import SubType, PartyType, ThirdPartySubType
from parties.models import EndUser, UltimateEndUser, Consignee, ThirdParty, Party
from picklists.models import PicklistItem
from queries.control_list_classifications.models import ControlListClassificationQuery
from queries.end_user_advisories.models import EndUserAdvisoryQuery
from queues.models import Queue
from static.control_list_entries.models import ControlListEntry
from static.countries.helpers import get_country
from static.statuses.enums import CaseStatusEnum
from static.statuses.libraries.get_case_status import get_case_status_from_status_enum
from static.units.enums import Units
from static.urls import urlpatterns as static_urlpatterns
from teams.models import Team
from test_helpers import colours
from test_helpers.helpers import random_name
from users.enums import UserStatuses
from users.libraries.user_to_token import user_to_token
from users.models import GovUser, BaseUser, ExporterUser, UserOrganisationRelationship


class DataTestClient(APITestCase, URLPatternsTestCase):
    """
    Test client which creates an initial organisation and user
    """
    urlpatterns = urlpatterns + static_urlpatterns
    client = APIClient

    def setUp(self):
        # Gov User Setup
        self.team = Team.objects.get(name='Admin')
        self.gov_user = GovUser(email='test@mail.com',
                                first_name='John',
                                last_name='Smith',
                                team=self.team)
        self.gov_user.save()
        self.gov_headers = {'HTTP_GOV_USER_TOKEN': user_to_token(self.gov_user)}

        # Exporter User Setup
        self.organisation = self.create_organisation_with_exporter_user()
        self.exporter_user = ExporterUser.objects.get()
        self.exporter_headers = {
            'HTTP_EXPORTER_USER_TOKEN': user_to_token(self.exporter_user),
            'HTTP_ORGANISATION_ID': self.organisation.id
        }

        self.queue = self.create_queue('Initial Queue', self.team)

        # Create a hardcoded control list entry rather than loading in the
        # spreadsheet each time
        ControlListEntry.create('ML1a', 'Description', None, False)

        if settings.TIME_TESTS:
            self.tick = datetime.now()

    def tearDown(self):
        """
        Print output time for tests if settings.TIME_TESTS is set to True
        """
        if settings.TIME_TESTS:
            self.tock = datetime.now()

            diff = self.tock - self.tick
            time = round(diff.microseconds / 1000, 2)
            colour = colours.green
            emoji = ''

            if time > 100:
                colour = colours.orange
            if time > 300:
                colour = colours.red
                emoji = ' 🔥'

            print(self._testMethodName + emoji + ' ' + colour(str(time) + 'ms') + emoji)

    def get(self, path, data=None, follow=False, **extra):
        response = self.client.get(path, data, follow, **extra)
        return response.json(), response.status_code

    def create_exporter_user(self, organisation=None, first_name=None, last_name=None):
        if not first_name and not last_name:
            first_name, last_name = random_name()

        exporter_user = ExporterUser(first_name=first_name,
                                     last_name=last_name,
                                     email=f'{first_name}@{last_name}.com')
        exporter_user.organisation = organisation
        exporter_user.save()

        if organisation:
            UserOrganisationRelationship(user=exporter_user,
                                         organisation=organisation).save()
            exporter_user.status = UserStatuses.ACTIVE

        return exporter_user

    def create_organisation_with_exporter_user(self, name='Organisation', org_type=None):

        organisation = Organisation(name=name,
                                    eori_number='GB123456789000',
                                    sic_number='2765',
                                    vat_number='123456789',
                                    registration_number='987654321')
        if org_type:
            organisation.type = org_type
        organisation.save()

        site, address = self.create_site('HQ', organisation)

        organisation.primary_site = site
        organisation.save()

        self.create_exporter_user(organisation)

        return organisation

    @staticmethod
    def add_exporter_user_to_org(organisation, exporter_user):
        UserOrganisationRelationship(user=exporter_user,
                                     organisation=organisation).save()

    @staticmethod
    def create_site(name, org):
        address = Address(address_line_1='42 Road',
                          address_line_2='',
                          country=get_country('GB'),
                          city='London',
                          region='Buckinghamshire',
                          postcode='E14QW')
        address.save()
        site = Site(name=name,
                    organisation=org,
                    address=address)
        site.save()
        return site, address

    @staticmethod
    def create_external_location(name, org):
        external_location = ExternalLocation(name=name,
                                             address='20 Questions Road, Enigma',
                                             country=get_country('GB'),
                                             organisation=org)
        external_location.save()
        return external_location

    @staticmethod
    def create_end_user(name, organisation):
        end_user = EndUser(name=name,
                           organisation=organisation,
                           address='42 Road, London, Buckinghamshire',
                           website='www.' + name + '.com',
                           sub_type=SubType.GOVERNMENT,
                           type=PartyType.END,
                           country=get_country('GB'))
        end_user.save()
        return end_user

    @staticmethod
    def create_ultimate_end_user(name, organisation):
        ultimate_end_user = UltimateEndUser(name=name,
                                            organisation=organisation,
                                            address='42 Road, London, Buckinghamshire',
                                            website='www.' + name + '.com',
                                            sub_type=SubType.GOVERNMENT,
                                            type=PartyType.ULTIMATE,
                                            country=get_country('GB'))
        ultimate_end_user.save()
        return ultimate_end_user

    @staticmethod
    def create_consignee(name, organisation):
        consignee = Consignee(name=name,
                              organisation=organisation,
                              address='42 Road, London, Buckinghamshire',
                              website='www.' + name + '.com',
                              sub_type=SubType.GOVERNMENT,
                              type=PartyType.CONSIGNEE,
                              country=get_country('GB'))
        consignee.save()
        return consignee

    @staticmethod
    def create_third_party(name, organisation):
        third_party = ThirdParty(name=name,
                                 organisation=organisation,
                                 address='42 Road, London, Buckinghamshire',
                                 website='www.' + name + '.com',
                                 sub_type=ThirdPartySubType.AGENT,
                                 type=PartyType.THIRD,
                                 country=get_country('GB'))
        third_party.save()
        return third_party

    def create_case_note(self, case: Case, text: str, user: BaseUser, is_visible_to_exporter: bool = False):
        case_note = CaseNote(case=case,
                             text=text,
                             user=user,
                             is_visible_to_exporter=is_visible_to_exporter)
        case_note.save()
        return case_note

    def create_end_user_advisory(self, note: str, reasoning: str, organisation: Organisation):
        end_user = self.create_end_user('name', self.organisation)
        end_user_advisory_query = EndUserAdvisoryQuery.objects.create(end_user=end_user,
                                                                      note=note,
                                                                      reasoning=reasoning,
                                                                      organisation=organisation,
                                                                      contact_telephone='1234567890',
                                                                      contact_name='Joe',
                                                                      contact_email='joe@something.com',
                                                                      contact_job_title='director',
                                                                      nature_of_business='guns')
        return end_user_advisory_query

    def create_end_user_advisory_case(self, note: str, reasoning: str, organisation: Organisation):
        eua_query = self.create_end_user_advisory(note, reasoning, organisation)
        return eua_query

    def create_queue(self, name: str, team: Team):
        queue = Queue(name=name,
                      team=team)
        queue.save()
        return queue

    def create_gov_user(self, email: str, team: Team):
        gov_user = GovUser(email=email,
                           team=team)
        gov_user.save()
        return gov_user

    def create_team(self, name: str):
        team = Team(name=name)
        team.save()
        return team

    def submit_draft(self, draft: Draft):
        draft_id = draft.id
        url = reverse('applications:applications')
        data = {'id': draft_id}
        self.client.post(url, data, **self.exporter_headers)
        return Application.objects.get(pk=draft_id)

    def create_case_document(self, case: Case, user: GovUser, name: str):
        case_doc = CaseDocument(case=case,
                                description='This is a document',
                                user=user,
                                name=name,
                                s3_key='thisisakey',
                                size=123456,
                                virus_scanned_at=None,
                                safe=None)
        case_doc.save()
        return case_doc

    def create_good_document(self, good: Good, user: ExporterUser, organisation: Organisation, name: str, s3_key: str):
        good_doc = GoodDocument(good=good,
                                description='This is a document',
                                user=user,
                                organisation=organisation,
                                name=name,
                                s3_key=s3_key,
                                size=123456,
                                virus_scanned_at=None,
                                safe=None)
        good_doc.save()
        return good_doc

    @staticmethod
    def create_document_for_party(party: Party, name='document_name.pdf', safe=True):
        document = PartyDocument(
            party=party,
            name=name,
            s3_key='s3_keykey.pdf',
            size=123456,
            virus_scanned_at=None,
            safe=safe
        )
        document.save()
        return document

    def create_flag(self, name: str, level: str, team: Team):
        flag = Flag(name=name, level=level, team=team)
        flag.save()
        return flag

    def create_case_assignment(self, queue, case, users):
        case_assignment = CaseAssignment(queue=queue,
                                         case=case)
        case_assignment.users.set(users)
        case_assignment.save()
        return case_assignment

    def create_goods_type(self, content_type_model, obj):
        goods_type = GoodsType(description='thing',
                               is_good_controlled=False,
                               control_code='ML1a',
                               is_good_end_product=True,
                               content_type=ContentType.objects.get(model=content_type_model),
                               object_id=obj.pk)
        goods_type.save()
        return goods_type

    def create_picklist_item(self, name, team: Team, picklist_type, status):
        picklist_item = PicklistItem(team=team,
                                     name=name,
                                     text='This is a string of text, please do not disturb the milk argument',
                                     type=picklist_type,
                                     status=status)
        picklist_item.save()
        return picklist_item

    def create_controlled_good(self, description: str, org: Organisation, control_code: str = 'ML1') -> object:
        good = Good(description=description,
                    is_good_controlled=GoodControlled.YES,
                    control_code=control_code,
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=org)
        good.save()
        return good

    @staticmethod
    def create_clc_query(description, organisation):
        good = Good(description=description,
                    is_good_controlled=GoodControlled.UNSURE,
                    control_code='ML1',
                    is_good_end_product=True,
                    part_number='123456',
                    organisation=organisation)
        good.save()

        clc_query = ControlListClassificationQuery.objects.create(details='this is a test text',
                                                                  good=good,
                                                                  organisation=organisation)
        return clc_query

    # Drafts

    def create_draft(self, organisation: Organisation, licence_type=ApplicationLicenceType.STANDARD_LICENCE,
                     reference_name='Standard Draft'):
        draft = Draft(name=reference_name,
                      licence_type=licence_type,
                      export_type=ApplicationExportType.PERMANENT,
                      have_you_been_informed=ApplicationExportLicenceOfficialType.YES,
                      reference_number_on_information_form='',
                      activity='Trade',
                      usage='Trade',
                      organisation=organisation)
        draft.save()
        return draft

    def create_standard_draft_without_end_user_document(self, organisation: Organisation,
                                                        reference_name='Standard Draft'):
        """
        Creates a standard draft application
        """
        draft = self.create_draft(organisation, ApplicationLicenceType.STANDARD_LICENCE, reference_name)

        # Add a good to the standard draft
        GoodOnDraft(good=self.create_controlled_good('a thing', organisation),
                    draft=draft,
                    quantity=10,
                    unit=Units.NAR,
                    value=500).save()

        # Set the draft's end user
        draft.end_user = self.create_end_user('test', organisation)

        # Add a site to the draft
        SiteOnDraft(site=organisation.primary_site, draft=draft).save()

        draft.save()
        return draft

    def create_standard_draft(self, organisation: Organisation, reference_name='Standard Draft', safe_document=True):
        draft = self.create_standard_draft_without_end_user_document(organisation, reference_name)

        self.create_document_for_party(draft.end_user, safe=safe_document)

        draft.consignee = self.create_consignee('consignee', organisation)
        draft.save()
        self.create_document_for_party(draft.consignee, safe=safe_document)

        return draft

    def create_open_draft(self, organisation: Organisation, reference_name='Open Draft'):
        """
        Creates an open draft application
        """
        draft = self.create_draft(organisation, ApplicationLicenceType.OPEN_LICENCE, reference_name)

        # Add a goods description
        self.create_goods_type('draft', draft)
        self.create_goods_type('draft', draft)

        # Add a country to the draft
        CountryOnDraft(draft=draft, country=get_country('GB')).save()

        # Add a site to the draft
        SiteOnDraft(site=organisation.primary_site, draft=draft).save()

        draft.save()
        return draft

    # Applications

    def create_standard_application(self, organisation: Organisation, reference_name='Standard Application'):
        """
        Creates a complete standard application
        """
        draft = self.create_standard_draft(organisation, reference_name)
        return self.submit_draft(draft)

    def create_open_application(self, organisation: Organisation, reference_name='Open Application'):
        """
        Creates a complete open application
        """
        draft = self.create_open_draft(organisation, reference_name)
        return self.submit_draft(draft)

    # Cases

    def create_standard_application_case(self, organisation: Organisation, reference_name='Standard Application Case'):
        """
        Creates a complete standard application case
        """
        draft = self.create_standard_draft(organisation, reference_name)

        application = self.submit_draft(draft)
        return Case.objects.get(application=application)

    def create_open_application_case(self, organisation: Organisation, reference_name='Open Application Case'):
        """
        Creates a complete open application case
        """
        draft = self.create_open_draft(organisation, reference_name)
        application = self.submit_draft(draft)
        return Case.objects.get(application=application)

    @staticmethod
    def create_advice(user, case, advice_field, advice_type, advice_level):
        advice = advice_level(
            user=user,
            case=case,
            type=advice_type,
            note='This is a note to the exporter',
            text='This is some text',
        )

        advice.team = user.team
        advice.save()

        if advice_field == 'end_user':
            advice.end_user = case.application.end_user

        if advice_field == 'good':
            advice.good = GoodOnApplication.objects.filter(application=case.application).first().good

        if advice_type == AdviceType.PROVISO:
            advice.proviso = 'I am easy to proviso'

        if advice_type == AdviceType.REFUSE:
            advice.denial_reasons.set(['1a', '1b', '1c'])

        advice.save()
        return advice

    @staticmethod
    def create_good_country_decision(case, goods_type, country, decision):
        GoodCountryDecision(case=case,
                            good=goods_type,
                            country=country,
                            decision=decision).save()
