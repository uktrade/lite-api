def json_to_security_grading_field_helper(json_object, field_name):
    return json_object[field_name]["raw_answer"] if field_name in json_object else None
