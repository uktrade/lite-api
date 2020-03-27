from cases.enums import CaseTypeEnum
from test_helpers.test_endpoints.helpers import call_endpoint


def application_get_endpoints(exporter, times):
    application_url = "/applications/"

    response, times = call_endpoint(exporter, application_url, times, "application_list")

    # get a standard and open application
    application_list = response.json()["results"]
    open_application = None
    standard_application = None
    for application in application_list:
        if application["case_type"]["reference"]["key"] == CaseTypeEnum.OIEL.reference:
            open_application = application
        elif application["case_type"]["reference"]["key"] == CaseTypeEnum.SIEL.reference:
            standard_application = application

    _, times = call_endpoint(exporter, application_url + standard_application["id"], times, "application_details")

    _, times = call_endpoint(
        exporter, application_url + standard_application["id"] + "/goods/", times, "application_goods"
    )

    # Goods type
    response, times = call_endpoint(
        exporter, application_url + open_application["id"] + "/goodstypes/", times, "application_goodstype_list"
    )

    goods_type_id = response.json()["goods"][0]["id"]

    _, times = call_endpoint(
        exporter,
        application_url + open_application["id"] + "/goodstype/" + goods_type_id,
        times,
        "application_goodstype_detail",
    )

    _, times = call_endpoint(
        exporter,
        application_url + open_application["id"] + "/goodstype/" + goods_type_id + "/document/",
        times,
        "application_goodstype_documents",
    )

    response, times = call_endpoint(
        exporter, application_url + standard_application["id"] + "/parties/", times, "application_parties_list"
    )

    party_id = response.json()["parties"][0]["id"]

    _, times = call_endpoint(
        exporter,
        application_url + standard_application["id"] + "/parties/" + party_id,
        times,
        "application_parties_detail",
    )

    _, times = call_endpoint(
        exporter,
        application_url + standard_application["id"] + "/parties/" + party_id + "/document/",
        times,
        "application_parties_document",
    )

    # sites locations and countries
    _, times = call_endpoint(
        exporter, application_url + standard_application["id"] + "/sites/", times, "application_sites",
    )

    _, times = call_endpoint(
        exporter, application_url + standard_application["id"] + "/external_locations/", times, "application_locations",
    )

    _, times = call_endpoint(
        exporter, application_url + open_application["id"] + "/countries/", times, "application_countries",
    )

    return times


def goods_get_endpoints(exporter, times):
    goods_url = "/goods/"

    response, times = call_endpoint(exporter, goods_url, times, "goods_list")

    good_id = response.json()["results"][0]["id"]
    good_document_id = response.json()["results"][0]["documents"][0]["id"]

    _, times = call_endpoint(exporter, goods_url + good_id, times, "goods_detail")

    _, times = call_endpoint(exporter, goods_url + good_id + "/documents/", times, "goods_documents")

    _, times = call_endpoint(exporter, goods_url + good_id + "/documents/" + good_document_id, times, "goods_document")

    return times


def organisation_get_endpoints(exporter, times):
    organisation_url = "/organisations/"

    response, times = call_endpoint(
        exporter, organisation_url + exporter["organisation-id"] + "/users/", times, "organisation_users"
    )

    user_in_organisation = response.json()["results"]["users"][0]["id"]

    _, times = call_endpoint(
        exporter,
        organisation_url + exporter["organisation-id"] + "/users/" + user_in_organisation,
        times,
        "organisation_user_detail",
    )

    response, times = call_endpoint(
        exporter, organisation_url + exporter["organisation-id"] + "/sites/", times, "organisation_sites"
    )

    site_id = response.json()["sites"][0]["id"]

    _, times = call_endpoint(
        exporter,
        organisation_url + exporter["organisation-id"] + "/sites/" + site_id,
        times,
        "organisation_site_detail",
    )

    _, times = call_endpoint(
        exporter,
        organisation_url + exporter["organisation-id"] + "/external_locations/",
        times,
        "organisation_external_locations",
    )

    response, times = call_endpoint(
        exporter, organisation_url + exporter["organisation-id"] + "/roles/", times, "organisation_roles",
    )

    role_id = response.json()["results"][0]["id"]

    response, times = call_endpoint(
        exporter, organisation_url + exporter["organisation-id"] + "/roles/" + role_id, times, "organisation_roles",
    )

    return times


def end_user_advisories_get_endpoints(exporter, times):
    end_user_advisories = "/queries/end-user-advisories/"

    response, times = call_endpoint(exporter, end_user_advisories, times, "EUA_list")

    eua_id = response.json()["end_user_advisories"][0]["id"]

    _, times = call_endpoint(exporter, end_user_advisories + eua_id, times, "EUA_detail")

    return times


def static_endpoints_get(exporter, times):
    static_url = "/static/"

    _, times = call_endpoint(user=exporter, endpoint=static_url + "case-types/", times=times, times_key="case-types")

    _, times = call_endpoint(
        user=exporter, endpoint=static_url + "control-list-entries/", times=times, times_key="control-list-entries"
    )

    _, times = call_endpoint(
        user=exporter,
        endpoint=static_url + "private-venture-gradings/",
        times=times,
        times_key="private-venture-gradings",
    )

    _, times = call_endpoint(user=exporter, endpoint=static_url + "countries/", times=times, times_key="countries",)

    _, times = call_endpoint(
        user=exporter, endpoint=static_url + "f680-clearance-types/", times=times, times_key="f680-clearance-types",
    )

    _, times = call_endpoint(user=exporter, endpoint=static_url + "decisions/", times=times, times_key="decisions",)

    _, times = call_endpoint(
        user=exporter, endpoint=static_url + "letter-layouts/", times=times, times_key="letter-layouts",
    )

    _, times = call_endpoint(
        user=exporter, endpoint=static_url + "denial-reasons/", times=times, times_key="denial-reasons",
    )

    _, times = call_endpoint(user=exporter, endpoint=static_url + "units/", times=times, times_key="units",)

    _, times = call_endpoint(user=exporter, endpoint=static_url + "statuses/", times=times, times_key="statuses",)

    _, times = call_endpoint(
        user=exporter,
        endpoint=static_url + "missing-document-reasons/",
        times=times,
        times_key="missing-document-reasons",
    )

    _, times = call_endpoint(user=exporter, endpoint=static_url + "item-types/", times=times, times_key="item-types",)

    return times


def users_get_endpoints(exporter, times):
    users_url = "/users/"

    response, times = call_endpoint(exporter, users_url, times, "users_list")

    user_id = response.json()["users"][0]["id"]

    _, times = call_endpoint(exporter, users_url + user_id, times, "users_detail")

    _, times = call_endpoint(exporter, users_url + "me/", times, "users_me")

    _, times = call_endpoint(exporter, users_url + "notifications/", times, "users_norifications")

    return times


def cases_get_endpoints(gov_user, times, is_gov=True):
    cases_url = "/cases/"

    response, times = call_endpoint(gov_user, cases_url, times, "cases_list", is_gov)

    case_id = response.json()["results"]["cases"][0]["id"]

    _, times = call_endpoint(gov_user, cases_url + case_id, times, "cases_detail", is_gov)

    _, times = call_endpoint(gov_user, cases_url + "destination/GB/", times, "destination_detail", is_gov)

    _, times = call_endpoint(gov_user, cases_url + case_id + "/case-notes/", times, "cases_notes", is_gov)
    _, times = call_endpoint(gov_user, cases_url + case_id + "/case-officer/", times, "cases_officer", is_gov)
    _, times = call_endpoint(gov_user, cases_url + case_id + "/activity/", times, "cases_activity", is_gov)
    _, times = call_endpoint(
        gov_user, cases_url + case_id + "/additional-contacts/", times, "cases_additional_contacts", is_gov
    )

    response, times = call_endpoint(gov_user, cases_url + case_id + "/documents/", times, "cases_documents", is_gov)
    if len(response.json()["documents"]):
        s3_key = response.json()["documents"][0]["s3_key"]
        doc_id = response.json()["documents"][0]["id"]
        _, times = call_endpoint(
            gov_user, cases_url + case_id + "/documents/" + s3_key, times, "cases_document", is_gov
        )
        _, times = call_endpoint(
            gov_user,
            cases_url + case_id + "/documents/" + doc_id + "/download/",
            times,
            "cases_document_download",
            is_gov,
        )

    _, times = call_endpoint(gov_user, cases_url + case_id + "/user-advice/", times, "cases_user_advice", is_gov)
    _, times = call_endpoint(gov_user, cases_url + case_id + "/team-advice/", times, "cases_team_advice", is_gov)
    _, times = call_endpoint(gov_user, cases_url + case_id + "/final-advice/", times, "cases_final_advice", is_gov)
    _, times = call_endpoint(
        gov_user, cases_url + case_id + "/view-final-advice/", times, "cases_view_final_advice", is_gov
    )
    _, times = call_endpoint(
        gov_user, cases_url + case_id + "/final-advice-documents/", times, "cases_final_advice_documents", is_gov
    )
    _, times = call_endpoint(
        gov_user, cases_url + case_id + "/goods-countries-decisions/", times, "cases_goods_countries_decisions", is_gov
    )

    response, times = call_endpoint(
        gov_user, cases_url + case_id + "/ecju-queries/", times, "cases_ecju_queries", is_gov
    )
    if response.json()["ecju_queries"]:
        query_id = response.json()["ecju_queries"][0]["id"]
        _, times = call_endpoint(
            gov_user, cases_url + case_id + "/ecju-queries/" + query_id, times, "cases_ecju_query", is_gov
        )

    _, times = call_endpoint(
        gov_user, cases_url + case_id + "/generated-documents/", times, "cases_generated_documents", is_gov
    )

    _, times = call_endpoint(gov_user, cases_url + case_id + "/finalise/", times, "cases_finalise", is_gov)

    return times


def flags_get_endpoints(gov_user, times, is_gov=True):
    flags_url = "/flags/"

    response, times = call_endpoint(gov_user, flags_url, times, "flags_list", is_gov)

    flag_id = response.json()["flags"][0]["id"]

    _, times = call_endpoint(gov_user, flags_url + flag_id, times, "flags_detail", is_gov)

    flags_rules_url = "rules/"

    response, times = call_endpoint(gov_user, flags_url + flags_rules_url, times, "flagging_rules_list", is_gov)

    flagging_rule_id = response.json()["results"][0]["id"]

    _, times = call_endpoint(
        gov_user, flags_url + flags_rules_url + flagging_rule_id, times, "flagging_rules_detail", is_gov
    )

    return times


def gov_users_get_endpoints(gov_user, times, is_gov=True):
    gov_users_url = "/gov-users/"

    response, times = call_endpoint(gov_user, gov_users_url, times, "gov_users_list", is_gov)

    user_id = response.json()["results"][0]["id"]

    _, times = call_endpoint(gov_user, gov_users_url + user_id, times, "gov_users_detail", is_gov)

    gov_user_roles_url = "roles/"
    gov_user_permission_url = "permissions/"
    gov_user_me_url = "me/"

    response, times = call_endpoint(gov_user, gov_users_url + gov_user_roles_url, times, "gov_users_roles_list", is_gov)

    role_id = response.json()["roles"][0]["id"]

    _, times = call_endpoint(
        gov_user, gov_users_url + gov_user_roles_url + role_id, times, "gov_users_roles_details", is_gov
    )
    _, times = call_endpoint(gov_user, gov_users_url + gov_user_permission_url, times, "gov_users_detail", is_gov)
    _, times = call_endpoint(gov_user, gov_users_url + gov_user_me_url, times, "gov_users_detail", is_gov)

    return times


def letter_templates_get_endpoints(gov_user, times, is_gov=True):
    letter_temaples_url = "/letter-templates/"

    response, times = call_endpoint(gov_user, letter_temaples_url, times, "letter_templates_list", is_gov)

    letter_template_id = response.json()["results"][0]["id"]

    _, times = call_endpoint(
        gov_user, letter_temaples_url + letter_template_id, times, "letter_templates_detail", is_gov
    )

    return times


def picklist_get_endpoints(gov_user, times, is_gov=True):
    picklists_url = "/picklist/"

    response, times = call_endpoint(gov_user, picklists_url, times, "picklist_list", is_gov)

    picklist_item_id = response.json()["picklist_items"][0]["id"]

    _, times = call_endpoint(gov_user, picklists_url + picklist_item_id, times, "picklist_detail", is_gov)

    return times


def queues_get_endpoints(gov_user, times, is_gov=True):
    queues_url = "/queues/"

    response, times = call_endpoint(gov_user, queues_url, times, "queue_list", is_gov)

    queue_id = response.json()["queues"][0]["id"]

    _, times = call_endpoint(gov_user, queues_url + queue_id, times, "queue_detail", is_gov)

    _, times = call_endpoint(
        gov_user, queues_url + queue_id + "/case-assignments/", times, "queue_case_assignments", is_gov
    )

    return times


def teams_get_endpoints(gov_user, times, is_gov=True):
    teams_url = "/teams/"

    response, times = call_endpoint(gov_user, teams_url, times, "teams_list", is_gov)

    team_id = response.json()["teams"][0]["id"]

    _, times = call_endpoint(gov_user, teams_url + team_id, times, "team_detail", is_gov)

    _, times = call_endpoint(gov_user, teams_url + team_id + "/users/", times, "team_users", is_gov)

    return times
