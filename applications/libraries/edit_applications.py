from applications.enums import GoodsTypeCategory
from applications.models import BaseApplication, StandardApplication, OpenApplication
from datetime import date

from audit_trail import service as audit_trail_service
from audit_trail.enums import AuditType
from cases.enums import CaseTypeSubTypeEnum, CaseTypeEnum
from cases.models import Case
from flags.enums import SystemFlags
from conf.helpers import str_to_bool, convert_date_to_string
from goods.enums import ItemCategory
from goods.models import Good
from lite_content.lite_api.strings import Applications as strings
from static.trade_control.enums import TradeControlActivity

END_USE_FIELDS = {
    "is_military_end_use_controls": strings.Generic.EndUseDetails.Audit.INFORMED_TO_APPLY_TITLE,
    "military_end_use_controls_ref": strings.Generic.EndUseDetails.Audit.INFORMED_TO_APPLY_REF,
    "is_informed_wmd": strings.Generic.EndUseDetails.Audit.INFORMED_WMD_TITLE,
    "informed_wmd_ref": strings.Generic.EndUseDetails.Audit.INFORMED_WMD_REF,
    "is_suspected_wmd": strings.Generic.EndUseDetails.Audit.SUSPECTED_WMD_TITLE,
    "suspected_wmd_ref": strings.Generic.EndUseDetails.Audit.SUSPECTED_WMD_REF,
    "is_eu_military": strings.Generic.EndUseDetails.Audit.EU_MILITARY_TITLE,
    "is_compliant_limitations_eu": strings.Generic.EndUseDetails.Audit.COMPLIANT_LIMITATIONS_EU_TITLE,
    "compliant_limitations_eu_ref": strings.Generic.EndUseDetails.Audit.COMPLIANT_LIMITATIONS_EU_REF,
    "intended_end_use": strings.Generic.EndUseDetails.Audit.INTENDED_END_USE_TITLE,
}

TEMP_EXPORT_DETAILS_FIELDS = {
    "temp_export_details": strings.Generic.TemporaryExportDetails.Audit.TEMPORARY_EXPORT_DETAILS,
    "is_temp_direct_control": strings.Generic.TemporaryExportDetails.Audit.PRODUCTS_UNDER_DIRECT_CONTROL,
    "temp_direct_control_details": strings.Generic.TemporaryExportDetails.Audit.PRODUCTS_UNDER_DIRECT_CONTROL_DETAILS,
    "proposed_return_date": strings.Generic.TemporaryExportDetails.Audit.PROPOSED_RETURN_DATE,
}


def get_old_field_values(application, fields):
    return {old_field: getattr(application, old_field) for old_field in fields.keys()}


def get_new_field_values(validated_data, fields):
    new_end_use_details = {}
    for end_use_field in fields.keys():
        if end_use_field in validated_data:
            new_end_use_details[end_use_field] = validated_data[end_use_field]
    return new_end_use_details


def audit_end_use_details(user, case, old_end_use_details_fields, new_end_use_details_fields):
    for key, new_end_use_value in new_end_use_details_fields.items():
        old_end_use_value = old_end_use_details_fields[key]
        if new_end_use_value != old_end_use_value:
            old_end_use_value, new_end_use_value = _transform_values(old_end_use_value, new_end_use_value)
            audit_trail_service.create(
                actor=user,
                verb=AuditType.UPDATE_APPLICATION_END_USE_DETAIL,
                target=case,
                payload={
                    "end_use_detail": END_USE_FIELDS[key],
                    "old_end_use_detail": old_end_use_value,
                    "new_end_use_detail": new_end_use_value,
                },
            )


def _transform_values(old_end_use_value, new_end_use_value):
    if isinstance(old_end_use_value, bool):
        old_end_use_value = "Yes" if old_end_use_value else "No"

    if isinstance(new_end_use_value, bool):
        new_end_use_value = "Yes" if new_end_use_value else "No"

    return old_end_use_value, new_end_use_value


def save_and_audit_end_use_details(request, application, serializer):
    new_end_use_details_fields = get_new_field_values(serializer.validated_data, END_USE_FIELDS)
    if new_end_use_details_fields:
        old_end_use_details_fields = get_old_field_values(application, END_USE_FIELDS)
        serializer.save()
        audit_end_use_details(
            request.user, application.get_case(), old_end_use_details_fields, new_end_use_details_fields
        )


def save_and_audit_temporary_export_details(request, application, serializer):
    new_temp_export_details = get_new_field_values(serializer.validated_data, TEMP_EXPORT_DETAILS_FIELDS)
    if new_temp_export_details:
        old_temp_export_details = get_old_field_values(application, TEMP_EXPORT_DETAILS_FIELDS)
        serializer.save()

        for key, new_temp_export_val in new_temp_export_details.items():
            old_temp_export_val = old_temp_export_details[key]
            if new_temp_export_val != old_temp_export_val:

                if isinstance(new_temp_export_val, date) or isinstance(old_temp_export_val, date):
                    old_temp_export_val = convert_date_to_string(old_temp_export_val) if old_temp_export_val else ""
                    new_temp_export_val = convert_date_to_string(new_temp_export_val)
                else:
                    old_temp_export_val, new_temp_export_val = _transform_values(
                        old_temp_export_val, new_temp_export_val
                    )
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATE_APPLICATION_TEMPORARY_EXPORT,
                    target=application.get_case(),
                    payload={
                        "temp_export_detail": TEMP_EXPORT_DETAILS_FIELDS[key],
                        "old_temp_export_detail": old_temp_export_val,
                        "new_temp_export_detail": new_temp_export_val,
                    },
                )


def save_and_audit_have_you_been_informed_ref(request, application, serializer):
    old_have_you_been_informed = application.have_you_been_informed
    have_you_been_informed = request.data.get("have_you_been_informed")

    if have_you_been_informed:
        old_ref_number = application.reference_number_on_information_form or "no reference"

        serializer.save()

        new_ref_number = application.reference_number_on_information_form or "no reference"

        if old_have_you_been_informed and not str_to_bool(have_you_been_informed):
            audit_trail_service.create(
                actor=request.user,
                verb=AuditType.REMOVED_APPLICATION_LETTER_REFERENCE,
                target=application.get_case(),
                payload={"old_ref_number": old_ref_number},
            )
        else:
            if old_have_you_been_informed:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.UPDATE_APPLICATION_LETTER_REFERENCE,
                    target=application.get_case(),
                    payload={"old_ref_number": old_ref_number, "new_ref_number": new_ref_number},
                )
            else:
                audit_trail_service.create(
                    actor=request.user,
                    verb=AuditType.ADDED_APPLICATION_LETTER_REFERENCE,
                    target=application.get_case(),
                    payload={"new_ref_number": new_ref_number},
                )


def set_case_flags_on_submitted_standard_or_open_application(application: BaseApplication):
    case = application.get_case()

    # set military end use and suspected wmd flags
    _add_or_remove_flag(
        case=case, flag_id=SystemFlags.MILITARY_END_USE_ID, is_adding=application.is_military_end_use_controls,
    )
    _add_or_remove_flag(
        case=case,
        flag_id=SystemFlags.WMD_END_USE_ID,
        is_adding=application.is_informed_wmd or application.is_suspected_wmd,
    )

    if application.case_type.sub_type == CaseTypeSubTypeEnum.STANDARD:
        trade_control_activity = StandardApplication.objects.values_list("trade_control_activity", flat=True).get(
            pk=application.pk
        )

        _add_or_remove_flag(
            case=case,
            flag_id=SystemFlags.MARITIME_ANTI_PIRACY_ID,
            is_adding=application.case_type.id == CaseTypeEnum.SICL.id
            and trade_control_activity == TradeControlActivity.MARITIME_ANTI_PIRACY,
        )

        good_item_categories = (
            Good.objects.filter(id__in=application.goods.all().values_list("good_id", flat=True))
            .values_list("item_category", flat=True)
            .distinct()
        )

        _add_or_remove_flag(
            case=case,
            flag_id=SystemFlags.FIREARMS_ID,
            is_adding=ItemCategory.GROUP2_FIREARMS in good_item_categories
            and application.case_type.id in [CaseTypeEnum.SIEL.id, CaseTypeEnum.SITL.id],
        )

    elif application.case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
        if application.case_type.id == CaseTypeEnum.OIEL.id:
            contains_firearm_goods, goodstype_category = OpenApplication.objects.values_list(
                "contains_firearm_goods", "goodstype_category"
            ).get(pk=application.pk)

            # set firearms flag for OIEL if their category goods type is military or uk continental shelf
            _add_or_remove_flag(
                case=case,
                flag_id=SystemFlags.FIREARMS_ID,
                is_adding=contains_firearm_goods
                and goodstype_category in [GoodsTypeCategory.MILITARY, GoodsTypeCategory.UK_CONTINENTAL_SHELF],
            )

        if application.case_type.id == CaseTypeEnum.OICL.id:
            trade_control_activity = OpenApplication.objects.values_list("trade_control_activity", flat=True).get(
                pk=application.pk
            )

            _add_or_remove_flag(
                case=case,
                flag_id=SystemFlags.MARITIME_ANTI_PIRACY_ID,
                is_adding=trade_control_activity == TradeControlActivity.MARITIME_ANTI_PIRACY,
            )


def _add_or_remove_flag(case: Case, flag_id: str, is_adding: bool):
    if is_adding:
        if not case.flags.filter(id=flag_id).exists():
            case.flags.add(flag_id)
    else:
        case.flags.remove(flag_id)
