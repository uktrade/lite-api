def get_denial_entity_type(data):
    entity_type = ""
    for key in ["end_user_flag", "consignee_flag", "other_role"]:
        if data.get(key) and isinstance(data[key], str):
            data[key] = data[key].lower() == "true"
    if data.get("end_user_flag", False) is True:
        entity_type = "End-user"
    elif data.get("end_user_flag", False) is False and data.get("consignee_flag", False) is True:
        entity_type = "Consignee"
    elif (
        data.get("end_user_flag", False) is False
        and data.get("consignee_flag", False) is False
        and data.get("other_role", False) is True
    ):
        entity_type = "Third-party"

    return entity_type
