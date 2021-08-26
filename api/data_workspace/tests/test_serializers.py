from api.data_workspace.serializers import EcjuQuerySerializer

from api.cases.tests.factories import EcjuQueryFactory


def test_EcjuQuerySerializer(db):
    ecju_query = EcjuQueryFactory()
    serialized = EcjuQuerySerializer(ecju_query)
    assert serialized.data
    assert "question" in serialized.data
    assert "response" in serialized.data
