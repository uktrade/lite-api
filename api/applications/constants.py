TRANSHIPMENT_AND_TRADE_CONTROL_BANNED_COUNTRIES = ["GB"]


class Standard:
    CONSIGNEE_DOCUMENT_PROCESSING = (
        "We are still processing a consignee document. Try submitting again in a few minutes."
    )
    END_USER_DOCUMENT_PROCESSING = (
        "We are still processing an end-user document. Try submitting again in a few minutes."
    )
    THIRD_PARTY_DOCUMENT_PROCESSING = (
        "We are still processing a third party document. Try submitting again in a few minutes."
    )
    ULTIMATE_END_USER_DOCUMENT_PROCESSING = (
        "We are still processing an ultimate recipient document. Try submitting again in a few minutes."
    )
    ADDITIONAL_DOCUMENTS_PROCESSING = (
        "We are still processing an additional document. Try submitting again in a few minutes."
    )
    GOODS_DOCUMENT_PROCESSING = "We are still processing a good document. Try submitting again in a few minutes."


class F680:
    ADDITIONAL_INFORMATION_FIELDS = (
        "expedited",
        "expedited_date",
        "foreign_technology",
        "foreign_technology_description",
        "locally_manufactured",
        "locally_manufactured_description",
        "mtcr_type",
        "electronic_warfare_requirement",
        "uk_service_equipment",
        "uk_service_equipment_description",
        "uk_service_equipment_type",
        "prospect_value",
    )

    REQUIRED_FIELDS = [
        "expedited",
        "foreign_technology",
        "locally_manufactured",
        "mtcr_type",
        "electronic_warfare_requirement",
        "uk_service_equipment",
        "uk_service_equipment_type",
        "prospect_value",
    ]

    REQUIRED_SECONDARY_FIELDS = {
        "foreign_technology": "foreign_technology_description",
        "expedited": "expedited_date",
        "locally_manufactured": "locally_manufactured_description",
    }
