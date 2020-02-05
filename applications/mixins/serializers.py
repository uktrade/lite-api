from collections import defaultdict

from rest_framework import serializers

from applications.enums import ApplicationType
from applications.models import PartyOnApplication
from parties.enums import PartyType
from parties.serializers import PartySerializer


class PartiesSerializerMixin(metaclass=serializers.SerializerMetaclass):
    """
    Fields must be added to class using PartiesMixin:

    class Meta:
        fields = (...) + PartiesMixin.Meta.fields
    """

    end_user = serializers.SerializerMethodField(required=False)
    ultimate_end_users = serializers.SerializerMethodField(required=False)
    third_parties = serializers.SerializerMethodField(required=False)
    consignee = serializers.SerializerMethodField(required=False)
    inactive_parties = serializers.SerializerMethodField(required=False)

    class Meta:
        fields = ("end_user", "ultimate_end_users", "third_parties", "consignee", "inactive_parties")

    __cache = None

    def __init_cache(self, instance):
        """
        Initiate parties queryset cache, split parties by type including non data store type: inactive_parties
        """
        self.__cache = defaultdict(list)
        for poa in instance.all_parties():
            party = PartySerializer(poa.party).data
            if poa.deleted_at:
                self.__cache[PartyType.INACTIVE_PARTIES].append(party)
            else:
                self.__cache[party["type"]].append(party)

    def __parties(self, instance, party_type):
        if not ApplicationType.has_parties(instance.application_type):
            return

        if self.__cache and isinstance(self.__cache, defaultdict):
            try:
                return self.__cache[party_type]
            except KeyError:
                return

        self.__init_cache(instance)

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

    def get_inactive_parties(self, instance):
        return self.__parties(instance, PartyType.INACTIVE_PARTIES)
