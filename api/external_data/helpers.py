from api.external_data.enums import DenialEntityType


# def get_denial_entity_type_from_db(entity_type):
#     if entity_type == DenialEntityType.END_USER:
#         return "End-user"
#     elif entity_type == DenialEntityType.CONSIGNEE:
#         return "Consignee"
#     elif entity_type == DenialEntityType.THIRD_PARTY:
#         return "Third-party"
#     else:
#         return ""


def get_denial_entity_type(data):
    entity_type = ""
    for key in ["end_user_flag", "consignee_flag"]:
        if data.get(key) and isinstance(data[key], str):
            data[key] = data[key].lower() == "true"
    if data.get("end_user_flag", False) is True:
        entity_type = "End-user"
    elif data.get("end_user_flag", False) is False and data.get("consignee_flag", False) is True:
        entity_type = "Consignee"
    elif (
        data.get("end_user_flag", False) is False
        and data.get("consignee_flag", False) is False
        and isinstance(data.get("other_role", None), str)
    ):
        entity_type = "Third-party"

    return entity_type


def get_denial_entity_enum(data):

    if isinstance(data, dict):
        entity_type = ""
        normalised_entity_type_dict = {keys.lower(): values.lower() for keys, values in data.items()}

        is_end_user_flag = normalised_entity_type_dict.get("end_user_flag", "false") == "true"
        is_consignee_flag = normalised_entity_type_dict.get("consignee_flag", "false") == "true"
        is_other_role = len(normalised_entity_type_dict.get("other_role", "")) > 0

        if is_end_user_flag and is_consignee_flag:
            entity_type = DenialEntityType.END_USER
        elif not is_end_user_flag and is_consignee_flag:
            entity_type = DenialEntityType.CONSIGNEE
        elif is_end_user_flag and not is_consignee_flag:
            entity_type = DenialEntityType.END_USER
        elif not is_end_user_flag and not is_consignee_flag and is_other_role:
            entity_type = DenialEntityType.THIRD_PARTY

        return entity_type
