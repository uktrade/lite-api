import csv
from datetime import datetime, timezone
import re
import logging

from django.core.management.base import BaseCommand

from api.cases.models import Case


class Command(BaseCommand):
    help = """
        Given some optional arguments, generate a CSV file of which cases have
        data that use special characters in good name or party address

        TODO: make this general enough to search any relevant model field

        TODO: add option to search cases as well as licences

        Example usage:
        ./manage.py match_special_characters --from="2024-03-30T00:00:00"
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            type=str,
            help="""An iso format datetime (UTC) which can be used to filter
            results e.g. '2024-01-01T00:00:00' such that only results *after*
            this datetime are included""",
        )

        parser.add_argument(
            "--to",
            type=str,
            help="""An iso format datetime (UTC) which can be used to filter
            results e.g. '2024-01-01T00:00:00' such that only results *before*
            this datetime are included""",
        )

    def handle(self, *args, **options):
        queryset = Case.objects.all()
        queryset = queryset.filter(licences__status__in=["issued", "reinstated"])
        queryset = queryset.order_by("licences__hmrc_integration_sent_at")

        from_datetime_isoformat = options.pop("from", None)
        if from_datetime_isoformat:
            from_datetime = datetime.fromisoformat(from_datetime_isoformat)
            from_datetime = from_datetime.replace(tzinfo=timezone.utc)
            queryset = queryset.filter(licences__hmrc_integration_sent_at__gte=from_datetime)

        to_datetime_isoformat = options.pop("to", None)
        if to_datetime_isoformat:
            to_datetime = datetime.fromisoformat(to_datetime_isoformat)
            to_datetime = to_datetime.replace(tzinfo=timezone.utc)
            queryset = queryset.filter(licences__hmrc_integration_sent_at__lte=to_datetime)

        self.fieldnames = [
            "cases__licences__reference_code",
            "cases__licences__status",
            "cases__licences__hmrc_integration_sent_at",
            "cases__baseapplication__goods__matches",
            "cases__baseapplication__parties__party__matches",
        ]
        self.csv_rows = []

        for case in queryset:
            row = {}
            all_good_name_matches = self.search_goods(case, row)
            all_party_address_matches = self.search_parties(case, row)
            if all_good_name_matches or all_party_address_matches:
                self.append_row(case, row)

        self.write_to_csv()

    def search_goods(self, case, row):
        all_good_name_matches = []
        goods_on_application = case.baseapplication.goods.all()
        for goa in goods_on_application:
            good_name = goa.good.name
            good_name_matches = self.get_matches(good_name)
            if good_name_matches:
                all_good_name_matches.append(good_name_matches)
                logging.info("Matches found in good name: %s", str(good_name_matches))
        if all_good_name_matches:
            row.update({"cases__baseapplication__goods__matches": ", ".join([str(m) for m in all_good_name_matches])})
        return all_good_name_matches

    def search_parties(self, case, row):
        all_party_address_matches = []
        parties_on_application = case.baseapplication.parties.all()
        for poa in parties_on_application:
            party_address = poa.party.address
            party_address_matches = self.get_matches(party_address)
            if party_address_matches:
                all_party_address_matches.append(party_address_matches)
                logging.info("Matches found in party address: %s", str(party_address_matches))
        if all_party_address_matches:
            row.update(
                {
                    "cases__baseapplication__parties__party__matches": ", ".join(
                        [str(m) for m in all_party_address_matches]
                    )
                }
            )
        return all_party_address_matches

    def append_row(self, case, row):
        row.update({"cases__licences__reference_code": getattr(case.licences.last(), "reference_code", "")})
        row.update({"cases__licences__status": getattr(case.licences.last(), "status", "")})
        row.update(
            {
                "cases__licences__hmrc_integration_sent_at": str(
                    getattr(case.licences.last(), "hmrc_integration_sent_at", "")
                )
            }
        )
        self.csv_rows.append(row)

    def get_matches(self, string):
        pattern = r"[^a-zA-Z0-9 .,\-\\)\\('/+:=\\?\\!\"%&\\*;\\<\\>]"
        matches = re.findall(pattern, string)
        return matches

    def write_to_csv(self):
        filename_base = "match_special_characters_"
        identifier = datetime.now().isoformat().replace("-", "_").replace("T", "_").replace(":", "_").replace(".", "_")
        filename = filename_base + identifier + ".csv"
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in self.csv_rows:
                writer.writerow(row)
