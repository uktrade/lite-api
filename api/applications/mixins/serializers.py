from collections import defaultdict

from rest_framework import serializers

from django.db.models import Min, Case, When, BinaryField

from api.cases.enums import CaseTypeSubTypeEnum
from api.external_data.models import SanctionMatch
from api.external_data.serializers import SanctionMatchSerializer
from api.flags.serializers import FlagSerializer
from api.parties.enums import PartyType
from api.parties.serializers import PartySerializer


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
            party["flags"] += FlagSerializer(poa.flags, many=True).data
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
        if "user_type" in self.context and self.context["user_type"] == "exporter":
            return self.__parties(instance, PartyType.ULTIMATE_END_USER)
        else:
            return self.get_ordered_parties(instance, PartyType.ULTIMATE_END_USER)

    def get_third_parties(self, instance):
        if "user_type" in self.context and self.context["user_type"] == "exporter":
            return self.__parties(instance, PartyType.THIRD_PARTY)
        else:
            return self.get_ordered_parties(instance, PartyType.THIRD_PARTY)

    def get_consignee(self, instance):
        data = self.__parties(instance, PartyType.CONSIGNEE)
        return data[0] if data else None

    def get_inactive_parties(self, instance):
        return self.__parties(instance, PartyType.INACTIVE_PARTIES)

    def get_ordered_parties(self, instance, party_type):
        """
        Order the parties based on destination flag priority and where the party has
        no flag, by destination (party/country depending on standard/open application) name.

        """
        parties_on_application = (
            instance.all_parties()
            .filter(party__type=party_type, deleted_at__isnull=True)
            .annotate(
                highest_flag_priority=Min("party__flags__priority"),
                contains_flags=Case(When(party__flags__isnull=True, then=0), default=1, output_field=BinaryField()),
            )
            .order_by("-contains_flags", "highest_flag_priority", "party__name")
        )

        parties = [PartySerializer(poa.party).data for poa in parties_on_application]

        return parties

    def get_sanction_matches(self, application):
        queryset = SanctionMatch.objects.filter(party_on_application__application=application, is_revoked=False)
        return SanctionMatchSerializer(queryset, many=True).data
