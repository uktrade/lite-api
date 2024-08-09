import csv
import logging
import time

from django.core.management.base import BaseCommand
from django.db.models import Prefetch
from rest_framework import serializers

from api.applications.models import GoodOnApplication, PartyOnApplication
from api.staticdata.statuses.enums import CaseStatusEnum
from api.licences.enums import LicenceStatus
from api.licences.models import Licence


class PartyOnLicenceSerializer(serializers.ModelSerializer):
    reference_code = serializers.CharField(source="application.reference_code")
    licence_reference = serializers.SerializerMethodField()
    party_type = serializers.CharField(source="party.type")
    destination = serializers.CharField(source="party.country.name")

    class Meta:
        model = PartyOnApplication
        fields = (
            "reference_code",
            "licence_reference",
            "party_type",
            "destination",
        )

    def get_licence_reference(self, instance):
        if len(instance.application.case_ptr.prefetched_licences) > 1:
            raise Exception

        return instance.application.case_ptr.prefetched_licences[0].reference_code


class Command(BaseCommand):
    help = """
        Generate report of all extant licences and the destinations mentioned on those Cases.
        The cases where all the products are NLR are filtered out.
    """

    def add_arguments(self, parser):
        pass

    def get_parties_on_licences(self):
        applications_with_controlled_goods = GoodOnApplication.objects.filter(
            is_good_controlled=True,
        ).values_list("application_id", flat=True)

        # TODO: Ideally we need to filter by sub_status value of approved also
        # but most of the old cases won't have this value.
        active_licences_qs = Licence.objects.filter(
            case_id__in=applications_with_controlled_goods,
            status__in=[LicenceStatus.ISSUED, LicenceStatus.REINSTATED],
            case__status__status=CaseStatusEnum.FINALISED,
        )
        application_ids_of_issued_licences = active_licences_qs.values_list("case_id", flat=True)

        parties_qs = (
            PartyOnApplication.objects.filter(
                application_id__in=application_ids_of_issued_licences,
                deleted_at__isnull=True,
            )
            .prefetch_related(
                Prefetch(
                    "application__case_ptr__licences",
                    to_attr="prefetched_licences",
                    queryset=active_licences_qs,
                )
            )
            .order_by("-application__reference_code")
        )

        return parties_qs

    def write_to_csv(self, filename, data, headers):
        # data is expected to be list of dicts
        with open(filename, "w", newline="") as f:
            dict_writer = csv.DictWriter(f, headers)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def handle(self, *args, **options):
        start = time.time()

        queryset = self.get_parties_on_licences()
        data = PartyOnLicenceSerializer(queryset, many=True).data

        logging.info("Writing %d to extant_licences.csv ...", queryset.count())
        self.write_to_csv("extant_licences.csv", data, data[0].keys())

        logging.info("Report generation took %d sec", time.time() - start)
