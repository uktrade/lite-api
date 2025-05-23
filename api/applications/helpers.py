import logging

from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from elasticsearch_dsl import Search, Q
from elasticsearch.exceptions import NotFoundError

from api.appeals.constants import APPEAL_DAYS
from api.applications.models import GoodOnApplication
from api.applications.serializers.good import GoodOnStandardLicenceSerializer
from api.cases.enums import AdviceType, AdviceLevel
from api.documents.models import Document
from api.documents.libraries import s3_operations
from api.external_data.models import SanctionMatch
from api.licences.models import GoodOnLicence

logger = logging.getLogger(__name__)


def validate_and_create_goods_on_licence(application_id, licence_id, data):
    errors = {}
    good_on_applications = (
        GoodOnApplication.objects.filter(
            application_id=application_id,
            good__advice__type__in=[AdviceType.APPROVE, AdviceType.PROVISO],
            good__advice__level=AdviceLevel.FINAL,
            good__advice__case_id=application_id,
        )
        .distinct()
        .values("id", "quantity")
    )
    goods_on_licence = GoodOnLicence.objects.filter(licence_id=licence_id)
    for goa in good_on_applications:
        quantity_key = f"quantity-{goa['id']}"
        value_key = f"value-{goa['id']}"
        good_data = {
            "quantity": data.get(quantity_key),
            "value": data.get(value_key),
        }

        try:
            # Update
            existing_good_on_licence = goods_on_licence.get(good_id=goa["id"])
            serializer = GoodOnStandardLicenceSerializer(
                instance=existing_good_on_licence,
                data=good_data,
                context={"applied_for_quantity": goa["quantity"]},
                partial=True,
            )
        except GoodOnLicence.DoesNotExist:
            # Create
            good_data["licence"] = licence_id
            good_data["good"] = goa["id"]
            serializer = GoodOnStandardLicenceSerializer(
                data=good_data,
                context={"applied_for_quantity": goa["quantity"]},
            )

        if not serializer.is_valid():
            quantity_error = serializer.errors.get("quantity")
            if quantity_error:
                errors[quantity_key] = quantity_error
            value_error = serializer.errors.get("value")
            if value_error:
                errors[value_key] = value_error
        else:
            serializer.save()

    # Exclude any NLR products that are associated with the licence
    # Ideally these won't exist but in case of product assessment changes when the
    # Case is sent back then it is possible
    # Eg if we try to finalise it before consolidating final advice. In such cases
    # initially a draft licence gets created and NLR products are also associated with
    # the licence. After consolidation they would still remain because we update the
    # draft if it exists hence we need to delete them manually
    good_on_applications_ids = good_on_applications.values_list("id", flat=True)
    nlr_products = GoodOnLicence.objects.filter(licence_id=licence_id).exclude(good_id__in=good_on_applications_ids)
    if nlr_products.exists():
        logger.info(
            "Mismatch on the number of products on licence: Approved (%s), Products on licence (%s)",
            good_on_applications.count(),
            GoodOnLicence.objects.filter(licence_id=licence_id).count(),
        )
        logger.info("Removing %s NLR products from Licence Id (%s)", nlr_products.count(), licence_id)
        nlr_products.delete()

    return errors


def delete_uploaded_document(data):
    doc_key = data["s3_key"]
    doc_exists = Document.objects.filter(s3_key=doc_key).exists()
    if doc_exists:
        Document(s3_key=doc_key, name="toDelete").delete_s3()
    else:
        s3_operations.delete_file(None, doc_key)


def auto_match_sanctions(application):
    parties = []
    if application.end_user:
        parties.append(application.end_user.party)

    for item in application.ultimate_end_users:
        parties.append(item.party)

    for party in parties:
        query = build_query(name=party.signatory_name_euu)
        results = (
            Search(index=settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS)
            .query(query)
            .update_from_dict({"size": 50, "collapse": {"field": "reference"}})
        )

        try:
            matches = results.execute().hits
        except (KeyError, NotFoundError):
            pass
        else:
            for match in matches:
                if match.meta.score > 0.5:
                    party_on_application = application.parties.get(party=party)
                    reference = match["reference"][0]
                    if not party_on_application.sanction_matches.filter(elasticsearch_reference=reference).exists():
                        SanctionMatch.objects.create(
                            party_on_application=party_on_application,
                            elasticsearch_reference=reference,
                            name=match["name"],
                            flag_uuid=match["flag_uuid"],
                        )


def normalize_address(value):
    return value.upper().replace(" ", "")


def build_query(name):
    return Q("match", name=name)


def reset_appeal_deadline(application):
    """
    Resets application appeal deadline when a Case is refused
    """
    application.appeal_deadline = timezone.localtime() + timedelta(APPEAL_DAYS)
    application.save()
