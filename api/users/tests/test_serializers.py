from api.users.models import BaseUser, UserType
from api.users.serializers import BaseUserViewSerializer
from test_helpers.clients import DataTestClient


class BaseUserViewSerializerTests(DataTestClient):
    def test_serialize_exporter(self):
        serializer = BaseUserViewSerializer(instance=self.exporter_user)

        data = serializer.data

        self.assertEqual(data["type"], UserType.EXPORTER.value)

    def test_serialize_gov_user(self):
        serializer = BaseUserViewSerializer(instance=self.gov_user)

        data = serializer.data

        self.assertEqual(data["type"], UserType.INTERNAL.value)

    def test_serialize_system_user(self):
        system_user = BaseUser(email="test@mail.com", first_name="Test", last_name="Tester", type=UserType.SYSTEM)
        system_user.save()
        serializer = BaseUserViewSerializer(instance=system_user)

        data = serializer.data

        self.assertEqual(data["type"], UserType.SYSTEM.value)
