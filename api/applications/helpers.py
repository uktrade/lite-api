from api.applications.enums import ApplicationExportType
from api.applications.models import BaseApplication, GoodOnApplication
from api.applications.serializers.end_use_details import (
    F680EndUseDetailsUpdateSerializer,
    OpenEndUseDetailsUpdateSerializer,
    StandardEndUseDetailsUpdateSerializer,
)
from api.applications.serializers.exhibition_clearance import (
    ExhibitionClearanceCreateSerializer,
    ExhibitionClearanceViewSerializer,
    ExhibitionClearanceUpdateSerializer,
)
from api.applications.serializers.f680_clearance import (
    F680ClearanceCreateSerializer,
    F680ClearanceViewSerializer,
    F680ClearanceUpdateSerializer,
)
from api.applications.serializers.gifting_clearance import (
    GiftingClearanceCreateSerializer,
    GiftingClearanceViewSerializer,
    GiftingClearanceUpdateSerializer,
)
from api.applications.serializers.hmrc_query import (
    HmrcQueryCreateSerializer,
    HmrcQueryViewSerializer,
    HmrcQueryUpdateSerializer,
)
from api.applications.serializers.open_application import (
    OpenApplicationCreateSerializer,
    OpenApplicationUpdateSerializer,
    OpenApplicationViewSerializer,
)
from api.applications.serializers.standard_application import (
    StandardApplicationCreateSerializer,
    StandardApplicationUpdateSerializer,
    StandardApplicationViewSerializer,
)
from api.applications.serializers.good import GoodOnStandardLicenceSerializer
from api.applications.serializers.temporary_export_details import TemporaryExportDetailsUpdateSerializer
from api.cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum, AdviceType, AdviceLevel
from api.core.exceptions import BadRequestError
from api.documents.models import Document
from api.licences.models import GoodOnLicence
from lite_content.lite_api import strings
from api.documents.libraries import s3_operations


def get_application_view_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceViewSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceViewSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_view_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_application_create_serializer(case_type):
    sub_type = CaseTypeEnum.reference_to_class(case_type).sub_type

    if sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceCreateSerializer
    elif sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceCreateSerializer
    else:
        raise BadRequestError({"application_type": [strings.Applications.Generic.SELECT_A_LICENCE_TYPE]})


def get_application_update_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenApplicationUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
        return HmrcQueryUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.EXHIBITION:
        return ExhibitionClearanceUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.GIFTING:
        return GiftingClearanceUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680ClearanceUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_update_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_application_end_use_details_update_serializer(application: BaseApplication):
    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        return StandardEndUseDetailsUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        return OpenEndUseDetailsUpdateSerializer
    elif application.case_type.sub_type == CaseTypeSubTypeEnum.F680:
        return F680EndUseDetailsUpdateSerializer
    else:
        raise BadRequestError(
            {
                f"get_application_end_use_details_update_serializer does "
                f"not support this application type: {application.case_type.sub_type}"
            }
        )


def get_temp_export_details_update_serializer(export_type):
    if export_type == ApplicationExportType.TEMPORARY:
        return TemporaryExportDetailsUpdateSerializer
    else:
        raise BadRequestError(
            {f"get_temp_export_details_update_serializer does " f"not support this export type: {export_type}"}
        )


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
                data=good_data, context={"applied_for_quantity": goa["quantity"]},
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

    return errors


def delete_uploaded_document(data):
    doc_key = data["s3_key"]
    doc_exists = Document.objects.filter(s3_key=doc_key).exists()
    if doc_exists:
        Document(s3_key=doc_key, name="toDelete").delete_s3()
    else:
        s3_operations.delete_file(None, doc_key)
