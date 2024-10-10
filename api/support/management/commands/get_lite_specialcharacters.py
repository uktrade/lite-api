from api.applications.models import GoodOnApplication, PartyOnApplication, CaseStatusEnum
from django.core.management.base import BaseCommand
import csv
import re
from django.db.models import Q


class SpecialCharacterFinder:
    match_string = r"[^a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>]"
    fieldnames = []

    results = []
    unique_result = {}

    def __init__(self, filename, data):
        self.filename = filename
        self.results = self.check_data(data)
        self.write_to_csv()

    def check_regex(self, value):
        match_regex = re.sub(self.match_string, "", value)
        if len(match_regex) < len(value):
            return set(value).difference(set(match_regex))

    def get_value(self, entry):
        return entry

    def get_id(self, entry):
        return entry

    def check_data(self, data):
        results = []
        for entry in data:
            id = self.get_id(entry)
            if not self.unique_result.get(id):
                value = self.get_value(entry)
                if match := self.check_regex(value):
                    results.append(self.format_results(entry, match))
                    self.unique_result[id] = True
        return results

    def format_results(self, data, match):
        return {
            "org_name": data.application.organisation.name,
            "good_id": data.good.id,
            "reference_code": data.application.reference_code,
            "value": data.good.name,
            "match": match,
        }

    def write_to_csv(self):
        with open(f"{self.filename}.csv", "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.results)


class GoodSpecialCharacterFinder(SpecialCharacterFinder):
    fieldnames = ["org_name", "reference_code", "good_id", "value", "match"]

    def get_value(self, entry):
        return entry.good.name

    def get_id(self, entry):
        return str(entry.good.id)


class PartyNameSpecialCharacterFinder(SpecialCharacterFinder):
    fieldnames = ["org_name", "reference_code", "party_id", "value", "match"]

    def get_value(self, entry):
        return entry.party.name

    def get_id(self, entry):
        return str(entry.party.id)

    def format_results(self, data, match):
        return {
            "org_name": data.application.organisation.name,
            "party_id": data.party.id,
            "reference_code": data.application.reference_code,
            "value": data.party.name,
            "match": match,
        }


class PartyAddressSpecialCharacterFinder(SpecialCharacterFinder):
    match_string = r"[^a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>\r\n]"
    fieldnames = ["org_name", "reference_code", "party_id", "value", "match"]

    def get_value(self, entry):
        return entry.party.address

    def get_id(self, entry):
        return str(entry.party.id)

    def format_results(self, data, match):
        return {
            "org_name": data.application.organisation.name,
            "party_id": data.party.id,
            "reference_code": data.application.reference_code,
            "value": data.party.address,
            "match": match,
        }


class Command(BaseCommand):
    help = """
        Command to check special characters within LITE

        This will generate csvs for good.name, party.name and party.address which can be retrieved using:
        cf shh <app> -c "cat app/csvname.csv > csvname.csv

        to be passed forward to support so that exporters can be contacted to review the fields raised
    """

    def handle(self, *args, **options):

        name_match_string = r"^[a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>]+$"
        address_match_string = r"^[a-zA-Z0-9 .,\-\)\(\/'+:=\?\!\"%&\*;\<\>\r\n]+$"

        # get goods that don't match the string and are not finalised
        goa = GoodOnApplication.objects.filter(
            ~Q(good__name__iregex=name_match_string)
            & ~Q(application__status__status__in=CaseStatusEnum._terminal_statuses)
        )

        # get parties that don't match the string and are not finalised
        party_matches = PartyOnApplication.objects.filter(
            Q(~Q(party__name__iregex=name_match_string) | ~Q(party__address__iregex=address_match_string))
            & ~Q(application__status__status__in=CaseStatusEnum._terminal_statuses)
        )

        GoodSpecialCharacterFinder("good_names", goa)
        PartyNameSpecialCharacterFinder("party_names", party_matches)
        PartyAddressSpecialCharacterFinder("party_address", party_matches)


# # retrieve file:
# cf ssh lite-api-uat -c "cat app/good_names.csv" > good_names.csv
# cf ssh lite-api-uat -c "cat app/party_names.csv" > party_names.csv
# cf ssh lite-api-uat -c "cat app/party_address.csv" > party_address.csv
