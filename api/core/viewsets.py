from rest_framework import viewsets


class ModelViewSet(viewsets.ModelViewSet):
    serializer_context_processors = []

    def get_serializer_context(self):
        context = super().get_serializer_context()

        for serializer_context_processor in self.serializer_context_processors:
            context.update(serializer_context_processor(self.request))

        return context
