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
        fields = ("end_user", "ultimate_end_users", "third_parties", "consignee")

    __cache = None

    def __parties(self, instance, party_type):
        if not ApplicationType.has_parties(instance.application_type):
            return

        if self.__cache and isinstance(self.__cache, defaultdict):
            try:
                return self.__cache[party_type]
            except KeyError:
                return
        else:
            self.__cache = defaultdict(list)
        serializer = PartySerializer([poa.party for poa in instance.parties_on_application], many=True)
        for party in serializer.data:
            self.__cache[party["type"]].append(party)

        return self.__cache[party_type]

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
