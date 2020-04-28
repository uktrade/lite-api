from collections import defaultdict

from rest_framework import serializers

from cases.enums import CaseTypeSubTypeEnum
from parties.enums import PartyType
from parties.serializers import PartySerializer
from django.db.models import Min


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
        fields = (
            "end_user",
            "ultimate_end_users",
            "third_parties",
            "consignee",
            "inactive_parties",
        )

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
        if not CaseTypeSubTypeEnum.has_parties(instance.case_type.sub_type):
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
        return data[0] if data else None

    def get_ultimate_end_users(self, instance):
        return self.get_ordered_parties(instance, PartyType.ULTIMATE_END_USER)

    def get_third_parties(self, instance):
        return self.get_ordered_parties(instance, PartyType.THIRD_PARTY)

    def get_consignee(self, instance):
        data = self.__parties(instance, PartyType.CONSIGNEE)
        return data[0] if data else None

    def get_inactive_parties(self, instance):
        return self.__parties(instance, PartyType.INACTIVE_PARTIES)

    def get_ordered_parties(self, instance, party_type):
        """ Order the parties based on country flag priority and where the party has
        no flag, by country name.

        """
        poa_with_destination_flags = (
            instance.all_parties()
            .filter(party__type=party_type, party__flags__isnull=False)
            .annotate(highest_priority=Min("party__flags__priority"))
            .order_by("highest_priority", "party__name")
        )

        parties_with_flags = [PartySerializer(poa.party).data for poa in poa_with_destination_flags]

        poa_without_destination_flags = (
            instance.all_parties().filter(party__type=party_type, party__flags__isnull=True).order_by("party__name")
        )
        parties_without_flags = [PartySerializer(poa.party).data for poa in poa_without_destination_flags]

        return parties_with_flags + parties_without_flags
