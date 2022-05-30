import logging

from django.core.management.base import BaseCommand

from api.external_data import documents
from api.flags.enums import SystemFlags

log = logging.getLogger(__name__)


DUMMY_SANCTIONS = {
    "consolidated_list": {
        "individuals": {
            "individual": [
                {
                    "dataid": "6908555",
                    "versionnum": "1",
                    "first_name": "ABDUL",
                    "second_name": "AZIZ",
                    "third_name": None,
                    "un_list_type": "DPRK",
                    "reference_number": "KPi.033",
                    "listed_on": "2016-11-30",
                    "comments1": "Ri Won Ho is a DPRK Ministry of State Security Official stationed in Syria.",
                    "designation": {"value": "DPRK Ministry of State Security Official"},
                    "nationality": {"value": "Democratic People's Republic of Korea"},
                    "list_name": {"value": "UN List"},
                    "last_day_updated": {"value": None},
                    "individual_alias": {"quality": None, "alias_name": None},
                    "individual_address": [{"country": None}],
                    "individual_date_of_birth": {"type_of_date": "EXACT", "date": "1964-07-17"},
                    "individual_place_of_birth": None,
                    "individual_document": {"type_of_document": "Passport", "number": "381310014"},
                    "sort_key": None,
                    "sort_key_last_mod": None,
                }
            ],
        },
    },
}

def join_fields(data, fields):
    return " ".join(str(data[field]) for field in fields if data.get(field))


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.populate_dummy_sanctions()

    def populate_dummy_sanctions(self):
        successful = 0
        failed = 0
        try:
            for item in DUMMY_SANCTIONS:
                try:
                    address_list = []

                    for address_item in item.get("addresses", {}).get("address", []):
                        address_list.append(" ".join(address_item.values()))

                    primary_name = next(
                        filter(
                            lambda n: n.get("nametype", "").lower() == "primary name",
                            item["names"]["name"],
                        )
                    )

                    name = join_fields(primary_name, fields=["name1", "name2", "name3", "name4", "name5", "name6"])
                    address = ",".join(address_list)

                    unique_id = item.get("ofsigroupid", "UNKNOWN")
                    document = documents.SanctionDocumentType(
                        meta={"id": f"uk:{unique_id}"},
                        name=name,
                        address=address,
                        flag_uuid=SystemFlags.SANCTION_UK_MATCH,
                        reference=unique_id,
                        data=item,
                    )
                    document.save()
                    successful += 1
                except:

                    failed += 1
                    log.exception(
                        "Error loading uk sanction record -> %s",
                        exc_info=True,
                    )
            log.info(
                f"uk sanctions (successful:{successful} failed:{failed})",
            )
        except:
            log.exception(
                "Error loading uk sanctions -> %s",
                exc_info=True,
            )
