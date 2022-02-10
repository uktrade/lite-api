from rest_framework import serializers

from api.queues.models import Queue


class FlagAliasesSerializers(serializers.ModelSerializer):
    # rooms = RoomSerializer(read_only=True, source="room_set", many=True)

    class Meta:
        model = Queue
        fields = (
            "id",
            "alias",
        )
