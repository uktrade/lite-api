def get_application_answer(json_object, field_name):
    return json_object[field_name]["raw_answer"] if field_name in json_object else None
