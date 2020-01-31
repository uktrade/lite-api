from collections import defaultdict

from rest_framework import serializers

from applications.enums import ApplicationType
from parties.enums import PartyType
from parties.serializers import PartySerializer


class PartiesSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """
    Backwards compatibility class.

    Fields must be added to class using PartiesMixin:

    class Meta:
        fields = (...) + PartiesMixin.fields
    """
    end_user = serializers.SerializerMethodField(required=False)
    ultimate_end_users = serializers.SerializerMethodField(required=False)
    third_parties = serializers.SerializerMethodField(required=False)
    consignee = serializers.SerializerMethodField(required=False)

    class Meta:
        fields = ('end_user', 'ultimate_end_users', 'third_parties', 'consignee')

    def __parties(self, instance, party_type, cache=defaultdict(list)):
        if cache and party_type in cache:
            return cache[party_type]
        else:
            cache.clear()

        if instance.application_type not in [ApplicationType.HMRC_QUERY, ApplicationType.STANDARD_LICENCE]:
            return

        data = PartySerializer(
            [
                poa.party for poa in (
                    instance.parties
                    .filter(deleted_at__isnull=True)
                    .select_related("party__organisation")
                )
            ], many=True
        ).data
        for party in data:
            cache[party["type"]].append(party)

        return cache[party_type]

    def get_end_user(self, instance):
        data = self.__parties(instance, PartyType.END_USER)

        if not data:
            return

        return data[0] if data else None

    def get_ultimate_end_users(self, instance):
        return self.__parties(instance, PartyType.ULTIMATE_END_USER)

    def get_third_parties(self, instance):
        return self.__parties(instance, PartyType.THIRD_PARTY)

    def get_consignee(self, instance):
        data = self.__parties(instance, PartyType.CONSIGNEE)

        return data[0] if data else None