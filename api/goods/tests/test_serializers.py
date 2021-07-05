import unittest

from api.goods import serializers


class TestPvGradingDetailsSerializer(unittest.TestCase):
    def test_pv_grading_details_serializer(self):
        serializer_one = serializers.PvGradingDetailsSerializer(data={})

        self.assertEqual(serializer_one.is_valid(), False)
        self.assertEqual("custom_grading" in serializer_one.errors, True)

        serializer_two = serializers.PvGradingDetailsSerializer(data={"custom_grading": "foo"})

        self.assertEqual(serializer_two.is_valid(), False)
        self.assertEqual("custom_grading" in serializer_two.errors, False)
