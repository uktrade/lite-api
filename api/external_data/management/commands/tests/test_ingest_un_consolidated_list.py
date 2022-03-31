from unittest import mock

from elasticsearch_dsl import Index, Search
import pyexcel
import requests_mock

from django.conf import settings
from django.core.management import call_command
import pytest

from api.external_data.management.commands import ingest_sanctions
from api.external_data import documents
from test_helpers.clients import DataTestClient


class PopulateSanctionsTests(DataTestClient):
    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = iter(
            [
                {
                    "Address Line 1": "Branch Office 1: i) Chohar Mir Road",
                    "Address Line 2": "Kandahari Bazaar",
                    "Address Line 3": "Quetta City",
                    "Address Line 4": "Baluchistan Province, Pakistan; ii) Room number 1",
                    "Business registration number (s)": "Unknown",
                    "Country of birth": "N/A",
                    "Current believed flag of ship": "N/A",
                    "Current owner/operator (s)": "N/A",
                    "D.O.B": "N/A",
                    "Date Designated": "29/06/2012 00:00:00",
                    "Email address": "Unknown",
                    "Entity, Vessel\xa0or Individual": "Entity",
                    "Gender": "N/A",
                    "Honorary/Professional/Religious titles": "N/A",
                    "Hull identification number (HIN)": "N/A",
                    "IMO number": "N/A",
                    "Last Updated": "N/A",
                    "Length of ship": "N/A",
                    "Name 1": "N/A",
                    "Name 2": "",
                    "Name 3": "",
                    "Name 4": "",
                    "Name 5": "",
                    "Name 6": "N/A",
                    "National Identifier number": "N/A",
                    "Nationality(/ies)": "N/A",
                    "OFSI ID": "12703",
                    "Other Information": "Pakistan National Tax Number: 1774308",
                    "Other suspected locations": "Branch Office 11: i) Sarafi Market, Zaranj",
                    "Parent company": "Unknown",
                    "Passport number": "N/A",
                    "Phone number ": "Unknown",
                    "Position": "N/A",
                    "Postcode": "Unknown",
                    "Previous flags": "N/A",
                    "Previous owner/operator (s)": "N/A",
                    "Primary Address Country": "Pakistan",
                    "Primary Name": "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE",
                    "Regime Name": "The Afghanistan (Sanctions) (EU Exit) Regulations 2020",
                    "Regime Type (UK, UN)": "UN",
                    "Sanctions Imposed": "Asset freeze",
                    "Subsidiaries": "Unknown",
                    "Tonnage of ship ": "N/A",
                    "Town of birth": "N/A",
                    "Type of entity": "Unknown",
                    "Type of ship": "N/A",
                    "UK Statement of Reasons": "N/A",
                    "UN Reference ID": "2989469",
                    "Unique ID": "AFG0001",
                    "Website": "Unknown",
                    "Year Built": "N/A",
                    "a.k.a": "Haji Khairullah-Haji Sattar Sarafi",
                    "a.k.a (Non-Latin Script)": "حاجی خيرالله و حاجی ستار صرافی",
                    "sheet": "MasterList-Bank",
                }
            ]
        )

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayofconsolidatedlist": {
                "consolidatedlist": [
                    {
                        "address1": None,
                        "address2": None,
                        "address3": None,
                        "address4": None,
                        "address5": None,
                        "address6": None,
                        "aliastype": "Prime Alias",
                        "aliastypename": "Prime Alias",
                        "businessregnumber": None,
                        "country": None,
                        "countryofbirth": None,
                        "currentowners": None,
                        "datelisted": "2001-10-12T00:00:00",
                        "datelistedday": "12",
                        "datelistedmonth": "10",
                        "datelistedyear": "2001",
                        "dateofbirth": None,
                        "dateofbirthid": None,
                        "dayofbirth": None,
                        "emailaddress": None,
                        "fcoid": "AQD0104",
                        "flagofvessel": None,
                        "fulladdress": None,
                        "fullname": "Haji Agha Abdul Manan",
                        "furtheridentifiyinginformation": "Pakistan. Review pursuant to Security",
                        "gender": None,
                        "groupid": "6897",
                        "groupstatus": "Asset Freeze Targets",
                        "grouptypedescription": "Individual",
                        "grpstatus": "A",
                        "hin": None,
                        "id": "109",
                        "imonumber": None,
                        "lastupdated": "2020-12-31T00:00:00",
                        "lastupdatedday": "31",
                        "lastupdatedmonth": "12",
                        "lastupdatedyear": "2020",
                        "lengthofvessel": None,
                        "listingtype": "UK and UN",
                        "monthofbirth": None,
                        "name1": "Abdul Manan",
                        "name2": None,
                        "name3": None,
                        "name4": None,
                        "name5": None,
                        "name6": "Agha",
                        "nametitle": "Haji",
                        "nationalidnumber": None,
                        "nationality": None,
                        "orgtype": None,
                        "otherinformation": "(UN Ref):QDi.018. Also referred to as Abdul Man’am",
                        "parentcompany": None,
                        "passportdetails": None,
                        "phonenumber": None,
                        "position": None,
                        "postcode": None,
                        "previousflags": None,
                        "previousowners": None,
                        "regimename": "ISIL (Da'esh) and Al-Qaida",
                        "subsidiaries": None,
                        "tonnageofvessel": None,
                        "townofbirth": None,
                        "typeofvessel": None,
                        "ukstatementofreasons": None,
                        "website": None,
                        "yearbuilt": None,
                        "yearofbirth": None,
                    }
                ]
            }
        }
        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [
                        {
                            "dataid": "6908555",
                            "versionnum": "1",
                            "first_name": "RI",
                            "second_name": "WON HO",
                            "third_name": None,
                            "un_list_type": "DPRK",
                            "reference_number": "KPi.033",
                            "listed_on": "2016-11-30",
                            "comments1": "Ri Won Ho is a DPRK Ministry of State Security Official stationed in Syria.",
                            "designation": {"value": "DPRK Ministry of State Security Official"},
                            "nationality": {"value": "Democratic People's Republic of Korea"},
                            "list_name": {"value": "UN List"},
                            "last_day_updated": {"value": None},
                            "individual_alias": {"quality": None, "alias_name": None},
                            "individual_address": [{"country": None}],
                            "individual_date_of_birth": {"type_of_date": "EXACT", "date": "1964-07-17"},
                            "individual_place_of_birth": None,
                            "individual_document": {"type_of_document": "Passport", "number": "381310014"},
                            "sort_key": None,
                            "sort_key_last_mod": None,
                        }
                    ],
                },
                "entities": {
                    "entity": [
                        {
                            "comments1": "The Propaganda and Agitation Department has full control over",
                            "dataid": "6908629",
                            "entity_address": [
                                {"city": "Pyongyang", "country": "Democratic People's Republic of Korea"}
                            ],
                            "entity_alias": {"alias_name": None, "quality": None},
                            "first_name": "PROPAGANDA AND AGITATION DEPARTMENT (PAD)",
                            "last_day_updated": {"value": None},
                            "list_name": {"value": "UN List"},
                            "listed_on": "2017-09-11",
                            "reference_number": "KPe.053",
                            "sort_key": None,
                            "sort_key_last_mod": None,
                            "un_list_type": "DPRK",
                            "versionnum": "1",
                        }
                    ]
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        Index(settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS).refresh()

        search = Search(index=documents.SanctionDocumentType.Index.name)

        results_one = search.query("match", name="RI WON HO").execute()
        self.assertEqual(len(results_one.hits), 1)
        self.assertEqual(results_one.hits[0]["name"], "RI WON HO")
        self.assertEqual(results_one.hits[0]["flag_uuid"], "00000000-0000-0000-0000-000000000039")
        self.assertEqual(results_one.hits[0]["reference"], "6908555")

        results_two = search.query("match", name="PROPAGANDA AND AGITATION DEPARTMENT").execute()
        self.assertEqual(len(results_two.hits), 1)
        self.assertEqual(results_two.hits[0]["name"], "PROPAGANDA AND AGITATION DEPARTMENT (PAD)")
        self.assertEqual(results_two.hits[0]["flag_uuid"], "00000000-0000-0000-0000-000000000039")
        self.assertEqual(results_two.hits[0]["reference"], "6908629")

        results_three = search.query("match", name="Haji Agha Abdul Manan").execute()
        self.assertEqual(len(results_three.hits), 2)
        self.assertEqual(results_three.hits[0]["name"], "Haji Agha Abdul Manan")
        self.assertEqual(results_three.hits[0]["flag_uuid"], "00000000-0000-0000-0000-000000000040")
        self.assertEqual(results_three.hits[0]["reference"], "109")

        self.assertEqual(results_three.hits[1]["name"], "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE")
        self.assertEqual(results_three.hits[1]["flag_uuid"], "00000000-0000-0000-0000-000000000041")
        self.assertEqual(results_three.hits[1]["reference"], "AFG0001")

    def test_get_un_sanctions(self):
        with requests_mock.Mocker() as m:
            m.get(settings.SANCTION_LIST_SOURCES["un_sanctions_file"], content=b"<note><to>Tove</to></note>")
            ingest_sanctions.get_un_sanctions()

    def test_get_office_financial_sanctions_implementation(self):
        with requests_mock.Mocker() as m:
            m.get(
                settings.SANCTION_LIST_SOURCES["office_financial_sanctions_file"],
                content=b"<note><to>Tove</to></note>",
            )
            ingest_sanctions.get_office_financial_sanctions_implementation()

    def test_get_uk_sanctions_list(self):
        book = pyexcel.get_book(
            bookdict={
                "Sheet 1": [[], [], ["a", "b", "c"], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
                "Sheet 2": [[], [], ["x", "y", "z"], [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            }
        )
        with mock.patch.object(pyexcel, "get_book", return_value=book):
            parsed = ingest_sanctions.get_uk_sanctions_list()

        self.assertEqual(
            list(parsed),
            [
                {"a": 1.0, "b": 2.0, "c": 3.0, "sheet": "Sheet 1"},
                {"a": 4.0, "b": 5.0, "c": 6.0, "sheet": "Sheet 1"},
                {"a": 7.0, "b": 8.0, "c": 9.0, "sheet": "Sheet 1"},
                {"x": 1.0, "y": 2.0, "z": 3.0, "sheet": "Sheet 2"},
                {"x": 4.0, "y": 5.0, "z": 6.0, "sheet": "Sheet 2"},
            ],
        )
