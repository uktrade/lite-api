import logging

from django.core.management.base import BaseCommand

from api.external_data import documents
from api.flags.enums import SystemFlags

log = logging.getLogger(__name__)


DUMMY_SANCTIONS = [
    {
        "lastupdated": "2020-12-31T00:00:00",
        "uniqueid": "AFG0001",
        "ofsigroupid": "1234",
        "unreferencenumber": None,
        "names": {
            "name": [
                {
                    "name6": "ABDUL AZIZ",
                    "nametype": "Primary Name",
                },
                {
                    "name1": "ABDUL AHAD",
                    "nametype": "alias",
                },
            ]
        },
        "addresses": {
            "address": [
                {
                    "addressLine1": "Sheykhan Village, Pirkowti Area, Orgun District",
                    "addressLine2": "Paktika Province, Afghanistan",
                },
                {
                    "addressLine1": "Shega District",
                    "addressLine2": "Kandahar Province, Afghanistan",
                },
            ]
        },
    },
]

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
