from rest_framework import serializers

from api.core.viewsets import ModelViewSet


def test_model_viewset_calls_serializer_context_processors(mocker, rf):
    def mock_context_processor(request):
        return {"foo": "bar"}

    def mock_another_context_processor(request):
        return {"from_request": request.some_object.some_attribute}

    class Serializer(serializers.Serializer):
        foo = serializers.SerializerMethodField()
        from_request = serializers.SerializerMethodField()

        def get_foo(self, instance):
            return self.context["foo"]

        def get_from_request(self, instance):
            return self.context["from_request"]

    class SerializerContextProcessors(ModelViewSet):
        serializer_class = Serializer
        serializer_context_processors = (
            mock_context_processor,
            mock_another_context_processor,
        )

        def get_object(self):
            return mocker.Mock()

    request = rf.get("/")

    class SomeObject:
        some_attribute = 42

    request.some_object = SomeObject()

    view = SerializerContextProcessors.as_view({"get": "retrieve"})
    response = view(request)

    assert response.data == {"foo": "bar", "from_request": 42}
