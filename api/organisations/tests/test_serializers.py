import pytest
from rest_framework import serializers

from api.organisations.serializers import PhoneNumberField


class TestPhoneNumberField:
    @pytest.mark.parametrize(
        "phone,exp_code,exp_number",
        [
            ("+44 1234 567921", 44, 1234567921),
            ("+44-1234-567921", 44, 1234567921),
            ("+44-7977-567921", 44, 7977567921),
            ("+33 5 97 75 67 92", 33, 597756792),
            ("01234 567921", 44, 1234567921),
            ("(01234) 567921", 44, 1234567921),
            ("(01234) - 567921", 44, 1234567921),
            ("01234567921", 44, 1234567921),
            ("(07777)567921", 44, 7777567921),
        ],
    )
    def test_phone_number_validation_success(self, phone, exp_code, exp_number):
        subj = PhoneNumberField()
        assert subj.to_internal_value(phone).country_code == exp_code
        assert subj.to_internal_value(phone).national_number == exp_number

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
        subj = PhoneNumberField()
        with pytest.raises(serializers.ValidationError) as validation_error:
            subj.to_internal_value(phone)

        assert "telephone" in str(validation_error.value)
