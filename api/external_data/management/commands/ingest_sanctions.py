import itertools
import logging
import ssl
import urllib3

from dateutil import parser

from django.conf import settings
from django.core.management.base import BaseCommand

from elasticsearch_dsl import connections

import requests
import xmltodict

from api.external_data import documents
from api.flags.enums import SystemFlags
import hashlib

logger = logging.getLogger(__name__)


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize, block=block, ssl_context=self.ssl_context
        )


def get_legacy_session():
    # https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


def get_un_sanctions():
    response = get_legacy_session().get(settings.SANCTION_LIST_SOURCES["un_sanctions_file"])
    response.raise_for_status()
    return xmltodict.parse(
        response.content,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
        force_list=["entity_address", "individual_address"],
    )


def get_office_financial_sanctions_implementation():
    response = requests.get(settings.SANCTION_LIST_SOURCES["office_financial_sanctions_file"])
    response.raise_for_status()
    return xmltodict.parse(
        response.content,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
    )


def get_uk_sanctions_list():
    response = requests.get(settings.SANCTION_LIST_SOURCES["uk_sanctions_file"])
    response.raise_for_status()
    doc = xmltodict.parse(
        response.content,
        postprocessor=(lambda path, key, value: (key.lower(), value)),
        xml_attribs=False,
        cdata_key="p",
        force_list=["name", "address"],
    )
    return doc["designations"]["designation"]


def join_fields(data, fields):
    return " ".join(str(data[field]) for field in fields if data.get(field))


def hash_values(data_values):
    data = "".join([val for val in data_values if val is not None])
    return hashlib.md5(data.encode()).hexdigest()  # nosec


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--rebuild", default=False, action="store_true")

    def rebuild_index(self):
        connection = connections.get_connection()
        connection.indices.delete(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS, ignore=[404])
        documents.SanctionDocumentType.init()

    def handle(self, *args, **options):
        if options["rebuild"]:
            self.rebuild_index()

        self.populate_united_nations_sanctions()
        self.populate_office_financial_sanctions_implementation()
        self.populate_uk_sanctions_list()

    def populate_united_nations_sanctions(self):
        try:
            parsed = get_un_sanctions()
            successful = 0
            failed = 0
            individuals = parsed["consolidated_list"]["individuals"]["individual"]
            entities = parsed["consolidated_list"]["entities"]["entity"]
            for item in itertools.chain(individuals, entities):
                try:
                    item.pop("nationality", None)
                    item.pop("title", None)

                    address_dicts = item.pop("entity_address", {}) or item.pop("individual_address", {})

                    addresses = []
                    for address_dict in address_dicts:
                        if address_dict:
                            addresses.append(" ".join([item for item in address_dict.values() if item]))

                    document = documents.SanctionDocumentType(
                        meta={"id": item["dataid"]},
                        name=join_fields(item, fields=["first_name", "second_name", "third_name"]),
                        address=addresses,
                        flag_uuid=SystemFlags.SANCTION_UN_SC_MATCH,
                        reference=item["dataid"],
                        data=item,
                    )
                    document.save()
                    successful += 1
                except:  # pragma: no cover # noqa
                    failed += 1
                    logger.exception(
                        "Error loading un sanction record -> %s",
                        item["dataid"],
                        exc_info=True,
                    )
            logger.info(
                f"un sanctions (successful:{successful} failed:{failed})",
            )
        except:  # pragma: no cover # noqa
            logger.exception(
                "Error loading un sanctions",
                exc_info=True,
            )

    def populate_office_financial_sanctions_implementation(self):
        successful = 0
        failed = 0
        try:
            parsed = get_office_financial_sanctions_implementation()
            for item in parsed["arrayoffinancialsanctionstarget"]["financialsanctionstarget"]:
                try:
                    item.pop("nationality", None)
                    address = join_fields(
                        item, fields=["address1", "address2", "address3", "address4", "address5", "address6"]
                    )
                    name = join_fields(item, fields=["name1", "name2", "name3", "name4", "name5", "name6"])
                    postcode = normalize_address(item["postcode"])
                    if postcode not in normalize_address(address):
                        address += " " + postcode

                    try:
                        item["lastupdated"] = normalize_datetime(item["lastupdated"])
                    except KeyError:
                        pass

                    try:
                        item["datedesignated"] = normalize_datetime(item["datedesignated"])
                    except KeyError:
                        pass

                    # We need to hash the data that uniquely identifies records atm we only care about names
                    unique_id = hash_values([item["groupid"], name])
                    document = documents.SanctionDocumentType(
                        meta={"id": f"ofs:{unique_id}"},
                        name=name,
                        address=address,
                        postcode=postcode,
                        flag_uuid=SystemFlags.SANCTION_OFSI_MATCH,
                        reference=item["groupid"],
                        data=item,
                    )
                    document.save()
                    successful += 1
                except:  # pragma: no cover # noqa
                    failed += 1
                    logger.exception(
                        "Error loading office financial sanction record -> %s",
                        f"ofs:{unique_id}",
                        exc_info=True,
                    )
            logger.info(
                f"office financial sanctions (successful:{successful} failed:{failed})",
            )
        except:  # pragma: no cover # noqa
            logger.exception(
                "Error office financial sanctions",
                exc_info=True,
            )

    def _get_primary_names_dict(self, names):
        backup_name = None
        for name in names:
            nametype = name.get("nametype")
            if not nametype:
                continue
            if nametype.lower() == "primary name":
                return name
            if nametype.lower() == "primary name variation":
                backup_name = name
        if backup_name:
            return backup_name

        raise Exception("Primary name not found")

    def populate_uk_sanctions_list(self):
        successful = 0
        failed = 0
        try:
            uk_sanctions_list = get_uk_sanctions_list()
            for item in uk_sanctions_list:
                unique_id = item.get("ofsigroupid", "UNKNOWN")

                try:
                    address_list = []

                    for address_item in item.get("addresses", {}).get("address", []):
                        address_list.append(" ".join(address_item.values()))

                    if "names" not in item:
                        logger.warning(
                            "No name found for record %s",
                            item,
                        )
                        continue
                    primary_name = self._get_primary_names_dict(item["names"]["name"])

                    name = join_fields(primary_name, fields=["name1", "name2", "name3", "name4", "name5", "name6"])
                    address = ",".join(address_list)

                    try:
                        item["lastupdated"] = normalize_datetime(item["lastupdated"])
                    except KeyError:
                        pass

                    try:
                        item["datedesignated"] = normalize_datetime(item["datedesignated"])
                    except KeyError:
                        pass

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
                except:  # noqa
                    failed += 1
                    logger.exception(
                        "Error loading uk sanction record -> %s",
                        f"uk:{unique_id}",
                        exc_info=True,
                    )
            logger.info(
                "uk sanctions (successful:%s failed:%s)",
                successful,
                failed,
            )
        except:  # pragma: no cover # noqa
            logger.exception(
                "Error loading uk sanctions",
                exc_info=True,
            )


def normalize_address(value):
    if isinstance(value, int):
        value = str(value)
    if not value or value.lower() in ["unknown", None, ""]:
        return ""

    return value.replace(" ", "")


def normalize_datetime(value):
    return parser.parse(value).isoformat()
