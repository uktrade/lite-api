import unittest

from api.goods import serializers


class TestPvGradingDetailsSerializer(unittest.TestCase):
    def test_pv_grading_details_serializer(self):
        serializer_one = serializers.PvGradingDetailsSerializer(data={})

        assert serializer_one.is_valid() is False
        assert "custom_grading" in serializer_one.errors

        serializer_two = serializers.PvGradingDetailsSerializer(data={"custom_grading": "foo"})

        assert serializer_two.is_valid() is False
        assert "custom_grading" not in serializer_two.errors
