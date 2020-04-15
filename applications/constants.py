TRANSHIPMENT_AND_TRADE_CONTROL_BANNED_COUNTRIES = ["GB"]


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
