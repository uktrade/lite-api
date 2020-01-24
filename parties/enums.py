class PartyType:
    CONSIGNEE = "consignee"
    END_USER = "end_user"
    ULTIMATE_END_USER = "ultimate_end_user"
    THIRD_PARTY = "third_party"

    choices = [
        (CONSIGNEE, "Consignee"),
        (END_USER, "End User"),
        (ULTIMATE_END_USER, "Ultimate End User"),
        (THIRD_PARTY, "Third Party"),
    ]


class SubType:
    GOVERNMENT = "government"
    COMMERCIAL = "commercial"
    INDIVIDUAL = "individual"
    OTHER = "other"

    choices = [
        (GOVERNMENT, "Government"),
        (COMMERCIAL, "Commercial Organisation"),
        (INDIVIDUAL, "Individual"),
        (OTHER, "Other"),
    ]


class PartyRole:
    INTERMEDIATE = "intermediate_consignee"
    END = "additional_end_user"
    AGENT = "agent"
    SUBMITTER = "submitter"
    CONSULTANT = "consultant"
    CONTACT = "contact"
    EXPORTER = "exporter"
    OTHER = "other"

    choices = [
        (INTERMEDIATE, "Intermediate Consignee"),
        (END, "Additional End User"),
        (AGENT, "Agent"),
        (SUBMITTER, "Authorised Submitter"),
        (CONSULTANT, "Consultant"),
        (CONTACT, "Contact"),
        (EXPORTER, "Exporter"),
        (OTHER, "Other"),
    ]
