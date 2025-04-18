class RecipientType:
    END_USER = "end-user"
    ULTIMATE_END_USER = "ultimate-end-user"
    THIRD_PARTY = "third-party"

    choices = [
        (END_USER, "End-user"),
        (ULTIMATE_END_USER, "Ultimate end-user"),
        (THIRD_PARTY, "Third party"),
    ]


class RecipientRole:
    AGENT_BROKER = "agent-or-broker"
    INTERMEDIATE_CONSIGNEE = "intermediate-consignee"
    AUTHORISED_SUBMITTER = "authorised-submitter"
    CONSULTANT = "consultant"
    CONTACT = "contact"
    EXPORTER = "exporter"
    OTHER = "other"

    choices = [
        (AGENT_BROKER, "Agent or broker"),
        (INTERMEDIATE_CONSIGNEE, "Intermediate consignee"),
        (AUTHORISED_SUBMITTER, "Authorised submitter"),
        (CONSULTANT, "Consultant"),
        (CONTACT, "Contact"),
        (EXPORTER, "Exporter"),
        (OTHER, "Other"),
    ]


class SecurityGrading:
    UNCLASSIFIED = "unclassified"
    OFFICIAL = "official"
    OFFICIAL_SENSITIVE = "official-sensitive"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"  # noqa
    TOP_SECRET = "top-secret"  # noqa
    OTHER = "other"

    product_choices = [
        (UNCLASSIFIED, "Unclassified"),
        (OFFICIAL, "Official"),
        (OFFICIAL_SENSITIVE, "Official - sensitive"),
        (RESTRICTED, "Restricted"),
        (CONFIDENTIAL, "Confidential"),
        (SECRET, "Secret"),
        (TOP_SECRET, "Top-secret"),
        (OTHER, "Other"),
    ]

    security_release_choices = [
        (OFFICIAL, "Official"),
        (OFFICIAL_SENSITIVE, "Official - sensitive"),
        (SECRET, "Secret"),
        (TOP_SECRET, "Top-secret"),
        (OTHER, "Other"),
    ]

    security_release_outcome_choices = [
        (OFFICIAL, "Official"),
        (OFFICIAL_SENSITIVE, "Official - sensitive"),
        (SECRET, "Secret"),
        (TOP_SECRET, "Top-secret"),
    ]


class ApprovalTypes:
    INITIAL_DISCUSSION_OR_PROMOTING = "initial_discussion_or_promoting"
    DEMONSTRATION_IN_UK = "demonstration_in_uk"
    DEMONSTRATION_OVERSEAS = "demonstration_overseas"
    TRAINING = "training"
    THROUGH_LIFE_SUPPORT = "through_life_support"
    SUPPLY = "supply"

    choices = [
        (INITIAL_DISCUSSION_OR_PROMOTING, "Initial discussion or promoting"),
        (DEMONSTRATION_IN_UK, "Demonstration in UK"),
        (DEMONSTRATION_OVERSEAS, "Demonstration overseas"),
        (TRAINING, "Training"),
        (THROUGH_LIFE_SUPPORT, "Through life support"),
        (SUPPLY, "Supply"),
    ]


class RecommendationType:
    APPROVE = "approve"
    REFUSE = "refuse"
    NOT_APPLICABLE = "not_applicable"

    choices = [
        (APPROVE, "Approve"),
        (REFUSE, "Refuse"),
        (NOT_APPLICABLE, "Not applicable"),
    ]


class SecurityReleaseOutcomes:
    APPROVE = "approve"
    REFUSE = "refuse"

    choices = [
        (APPROVE, "Approve"),
        (REFUSE, "Refuse"),
    ]


class SecurityReleaseOutcomeDuration:
    MONTHS_24 = 24
    MONTHS_48 = 48
