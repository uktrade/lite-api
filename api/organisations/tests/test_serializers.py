import pytest
from rest_framework import serializers

from api.organisations.serializers import OrganisationCreateUpdateSerializer


class SimpleOrganisationCreateUpdateSerializer(OrganisationCreateUpdateSerializer):
    user = serializers.CharField(required=False)
    site = serializers.CharField(required=False)


class TestOrganisationCreateUpdateSerializer:
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

    @pytest.mark.parametrize(
        "phone,exp_number",
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
        ],
    )
    def test_phone_number_validation_success(self, phone, exp_number):
        data = self.non_phone_data
        data["phone_number"] = phone

        subj = SimpleOrganisationCreateUpdateSerializer(data=data)

        assert subj.is_valid()
        assert subj._validated_data["phone_number"] == exp_number

    @pytest.mark.parametrize(
        "phone",
        [
            "9234 567921",
            "(9234) 567921",
            "67921",
            "banana",
            "01234@567921",
        ],
    )
    def test_phone_number_validation_failure(self, phone):
        data = self.non_phone_data
        data["phone_number"] = phone

        subj = SimpleOrganisationCreateUpdateSerializer(data=data)

        assert not subj.is_valid()
