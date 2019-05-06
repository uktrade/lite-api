def user_is_trying_to_change_own_status(id_of_user_to_have_status_changed, id_of_request_user):
    return id_of_user_to_have_status_changed == id_of_request_user
