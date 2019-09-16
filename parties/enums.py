class PartyType:
    CONSIGNEE = 'consignee'
    END = 'end_user'
    ULTIMATE = 'ultimate_end_user'
    THIRD = 'third_party'

    choices = [
        (CONSIGNEE, 'Consignee'),
        (END, 'End User'),
        (ULTIMATE, 'Ultimate End User'),
        (THIRD, 'Third Party'),
    ]


class SubType:
    GOVERNMENT = 'government'
    COMMERCIAL = 'commercial'
    INDIVIDUAL = 'individual'
    OTHER = 'other'

    choices = [
        (GOVERNMENT, 'Government'),
        (COMMERCIAL, 'Commercial Organisation'),
        (INDIVIDUAL, 'Individual'),
        (OTHER, 'Other'),
    ]


class ThirdPartySubType:
    INTERMEDIATE = 'intermediate_consignee'
    AGENT = 'agent'
    SUBMITTER = 'submitter'
    CONSULTANT = 'consultant'
    CONTACT = 'contact'
    EXPORTER = 'exporter'
    OTHER = 'other'

    choices = [
        (INTERMEDIATE, 'Intermediate Consignee'),
        (AGENT, 'Agent'),
        (SUBMITTER, 'Authorised Submitter'),
        (CONSULTANT, 'Consultant'),
        (CONTACT, 'Contact'),
        (EXPORTER, 'Exporter'),
        (OTHER, 'Other'),
    ]
