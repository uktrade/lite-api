from unittest import mock

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Index, Search
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
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020-12-31T00:00:00",
                "uniqueid": "AFG0001",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE",
                            "nametype": "Primary Name",
                        },
                        {
                            "name1": "SATTAR MONEY EXCHANGE",
                            "nametype": "alias",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "Branch Office 10",
                            "addressLine2": "Suite numbers 196-197",
                        },
                        {
                            "addressLine1": "Branch Office 13",
                            "addressLine2": "Sarafi Market",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [
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
                        "name1": "Haji",
                        "name2": "Agha",
                        "name3": None,
                        "name4": None,
                        "name5": None,
                        "name6": "Abdul Manan",
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
        self.assertEqual(results_three.hits[0]["reference"], "6897")

        self.assertEqual(results_three.hits[1]["name"], "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE")
        self.assertEqual(results_three.hits[1]["flag_uuid"], "00000000-0000-0000-0000-000000000041")
        self.assertEqual(results_three.hits[1]["reference"], "1234")

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_mixed_date_formats(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        # This is to test the case where the first documents to go into the
        # index set a particular date format and then subsequent documents that
        # are saved which don't match that date format fail to save
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "AFG0001",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE",
                            "nametype": "Primary Name",
                        },
                        {
                            "name1": "SATTAR MONEY EXCHANGE",
                            "nametype": "alias",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "Branch Office 10",
                            "addressLine2": "Suite numbers 196-197",
                        },
                        {
                            "addressLine1": "Branch Office 13",
                            "addressLine2": "Sarafi Market",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [
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
                        "datedesignated": "2020-12-10T00:00:00",
                        "lengthofvessel": None,
                        "listingtype": "UK and UN",
                        "monthofbirth": None,
                        "name1": "Haji",
                        "name2": "Agha",
                        "name3": None,
                        "name4": None,
                        "name5": None,
                        "name6": "Abdul Manan",
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

        doc = documents.SanctionDocumentType.get("uk:1234")
        self.assertEqual(
            doc.data.lastupdated,
            "2020-12-31T00:00:00",
        )
        self.assertEqual(
            doc.data.datedesignated,
            "2020-12-10T00:00:00",
        )

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_normalizes_dates(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "AFG0001",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "HAJI KHAIRULLAH HAJI SATTAR MONEY EXCHANGE",
                            "nametype": "Primary Name",
                        },
                        {
                            "name1": "SATTAR MONEY EXCHANGE",
                            "nametype": "alias",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "Branch Office 10",
                            "addressLine2": "Suite numbers 196-197",
                        },
                        {
                            "addressLine1": "Branch Office 13",
                            "addressLine2": "Sarafi Market",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [
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
                        "furtheridentifiyinginformation": "Pakistan. Review pursuant to Security",
                        "gender": None,
                        "groupid": "6897",
                        "groupstatus": "Asset Freeze Targets",
                        "grouptypedescription": "Individual",
                        "grpstatus": "A",
                        "hin": None,
                        "id": "109",
                        "imonumber": None,
                        "lastupdated": "2020/12/31",
                        "lastupdatedday": "31",
                        "lastupdatedmonth": "12",
                        "lastupdatedyear": "2020",
                        "datedesignated": "2020/12/10",
                        "lengthofvessel": None,
                        "listingtype": "UK and UN",
                        "monthofbirth": None,
                        "name1": "Haji",
                        "name2": "Agha",
                        "name3": None,
                        "name4": None,
                        "name5": None,
                        "name6": "Abdul Manan",
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

        doc = documents.SanctionDocumentType.get("uk:1234")
        self.assertEqual(
            doc.data.lastupdated,
            "2020-12-31T00:00:00",
        )
        self.assertEqual(
            doc.data.datedesignated,
            "2020-12-10T00:00:00",
        )

        doc = documents.SanctionDocumentType.get("ofs:28f40249140f9c08d1d0172fb834dea1")  # /PS-IGNORE
        self.assertEqual(
            doc.data.lastupdated,
            "2020-12-31T00:00:00",
        )
        self.assertEqual(
            doc.data.datedesignated,
            "2020-12-10T00:00:00",
        )

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
        with requests_mock.Mocker() as m:
            m.get(
                settings.SANCTION_LIST_SOURCES["uk_sanctions_file"],
                content=b"<designations><designation>Designation</designation></designations>",
            )
            ingest_sanctions.get_uk_sanctions_list()

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_primary_name_variation(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "Primary name variation test",
                            "nametype": "Primary Name Variation",
                        },
                        {
                            "name1": "Primary name variation test alias",
                            "nametype": "alias",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [],
            }
        }

        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [],
                },
                "entities": {
                    "entity": [],
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        doc = documents.SanctionDocumentType.get("uk:1234")
        self.assertEqual(doc.name, "Primary name variation test")

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_primary_name_takes_precedence_over_variation(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "Primary name variation test",
                            "nametype": "Primary Name Variation",
                        },
                        {
                            "name1": "Primary name",
                            "nametype": "Primary Name",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [],
            }
        }

        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [],
                },
                "entities": {
                    "entity": [],
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        doc = documents.SanctionDocumentType.get("uk:1234")
        self.assertEqual(doc.name, "Primary name")

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_primary_name_no_name_type_ignored(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "No name type",
                        },
                        {
                            "name1": "Primary name",
                            "nametype": "Primary Name",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [],
            }
        }

        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [],
                },
                "entities": {
                    "entity": [],
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        doc = documents.SanctionDocumentType.get("uk:1234")
        self.assertEqual(doc.name, "Primary name")

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_primary_name_no_name_record_ignored(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "No name type",
                        },
                        {
                            "name1": "Primary name",
                            "nametype": "No primary name type",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "5678",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name6": "No name type",
                        },
                        {
                            "name1": "Primary name",
                            "nametype": "Primary Name",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [],
            }
        }

        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [],
                },
                "entities": {
                    "entity": [],
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        with self.assertRaises(NotFoundError):
            documents.SanctionDocumentType.get("uk:1234")

        doc = documents.SanctionDocumentType.get("uk:5678")
        self.assertEqual(doc.name, "Primary name")

    @pytest.mark.elasticsearch
    @mock.patch.object(ingest_sanctions, "get_un_sanctions")
    @mock.patch.object(ingest_sanctions, "get_office_financial_sanctions_implementation")
    @mock.patch.object(ingest_sanctions, "get_uk_sanctions_list")
    def test_populate_sanctions_primary_name_no_names_record_ignored(
        self, mock_get_uk_sanctions_list, mock_get_office_financial_sanctions_implementation, mock_get_un_sanctions
    ):
        mock_get_uk_sanctions_list.return_value = [
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "1234",
                "unreferencenumber": None,
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
            {
                "lastupdated": "2020/12/31",
                "datedesignated": "2020/12/10",
                "uniqueid": "unique-id",
                "ofsigroupid": "5678",
                "unreferencenumber": None,
                "names": {
                    "name": [
                        {
                            "name1": "Primary name",
                            "nametype": "Primary Name",
                        },
                    ]
                },
                "addresses": {
                    "address": [
                        {
                            "addressLine1": "address line 1",
                            "addressLine2": "address line 2",
                        },
                        {
                            "addressLine1": "another address line 1",
                            "addressLine2": "another address line 2",
                        },
                    ]
                },
            },
        ]

        mock_get_office_financial_sanctions_implementation.return_value = {
            "arrayoffinancialsanctionstarget": {
                "financialsanctionstarget": [],
            }
        }

        mock_get_un_sanctions.return_value = {
            "consolidated_list": {
                "individuals": {
                    "individual": [],
                },
                "entities": {
                    "entity": [],
                },
            },
        }

        call_command("ingest_sanctions", rebuild=True)

        with self.assertRaises(NotFoundError):
            documents.SanctionDocumentType.get("uk:1234")

        doc = documents.SanctionDocumentType.get("uk:5678")
        self.assertEqual(doc.name, "Primary name")
