class PartyType:
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


class ThirdPartyType:
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
