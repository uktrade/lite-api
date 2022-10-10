def get_denial_entity_type(data):
    entity_type = ""
    for key in ["end_user_flag", "consignee_flag", "other_role"]:
        if isinstance(data[key], str):
            data[key] = data[key].lower() == "true"

    if data["end_user_flag"] is True:
        entity_type = "End-user"
    elif data["end_user_flag"] is False and data["consignee_flag"] is True:
        entity_type = "Consignee"
    elif data["end_user_flag"] is False and data["consignee_flag"] is False and data["other_role"] is True:
        entity_type = "Third-party"

    return entity_type
