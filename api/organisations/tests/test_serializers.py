import pytest
from rest_framework import serializers
from parameterized import parameterized
from test_helpers.clients import DataTestClient
from api.organisations.serializers import OrganisationCreateUpdateSerializer, OrganisationRegistrationNumberSerializer


class SimpleOrganisationCreateUpdateSerializer(OrganisationCreateUpdateSerializer):
    user = serializers.CharField(required=False)
    site = serializers.CharField(required=False)


class TestOrganisationCreateUpdateSerializer(DataTestClient):
    non_phone_data = {
        "name": "Bob",
        "eori_number": "XI808372974736884",
        "sic_number": "96095",
        "vat_number": "GB572898583",
        "registration_number": "DE390860",
        "type": "hmrc",
        "website": "",
        "phone_number": "",
    }

    @parameterized.expand(
        [
            ("+44 1234 567921", "+441234567921"),
            ("+44-1234-567921", "+441234567921"),
            ("+44-7977-567921", "+447977567921"),
            ("+33 5 97 75 67 92", "+33597756792"),
            ("01234 567921", "+441234567921"),
            ("(01234) 567921", "+441234567921"),
            ("(01234) - 567921", "+441234567921"),
            ("01234567921", "+441234567921"),
            ("(07777)567921", "+447777567921"),
        ]
    )
    def test_phone_number_validation_success(self, phone, exp_number):
        data = self.non_phone_data
        data["phone_number"] = phone

        subj = SimpleOrganisationCreateUpdateSerializer(data=data)

        self.assertTrue(subj.is_valid())
        self.assertEqual(subj._validated_data["phone_number"], exp_number)

    @parameterized.expand(
        [
            ("9234 567921"),
            ("(9234) 567921"),
            ("67921"),
            ("banana"),
            ("01234@567921"),
        ],
    )
    def test_phone_number_validation_failure(self, phone):
        data = self.non_phone_data
        data["phone_number"] = phone

        subj = SimpleOrganisationCreateUpdateSerializer(data=data)

        self.assertFalse(subj.is_valid())


class TestOrganisationRegistrationNumberSerializer(DataTestClient):
    @parameterized.expand(
        [("12345678", "12345678"), ("GB123456", "GB123456")],
    )
    def test_registration_number_validation_success(self, reg_number, expected):
        data = {"registration_number": reg_number}

        subj = OrganisationRegistrationNumberSerializer(data=data)
        self.assertTrue(subj.is_valid())
        self.assertEqual(subj._validated_data["registration_number"], expected)

    def test_registration_number_validation_fail(self):
        data = {"registration_number": ""}

        subj = OrganisationRegistrationNumberSerializer(data=data)
        self.assertFalse(subj.is_valid())
