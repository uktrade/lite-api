class PicklistType:
    PROVISO = 'proviso'
    ECJU = 'ecju_query'
    LETTER_PARAGRAPH = 'letter_paragraph'
    ANNUAL_REPORT_SUMMARY = 'annual_report_summary'
    STANDARD_ADVICE = 'standard_advice'
    FOOTNOTES = 'footnotes'

    choices = [
        (PROVISO, 'Proviso'),
        (ECJU, 'ECJU_Query'),
        (LETTER_PARAGRAPH, 'Under review'),
        (ANNUAL_REPORT_SUMMARY, 'Annual Report Summary'),
        (STANDARD_ADVICE, 'Standard Advice'),
        (FOOTNOTES, 'Footnotes'),
    ]


class PickListStatus:
    ACTIVATE = 'Activate'
    DEACTIVATE = 'Deactivate'

    choices = [
        (ACTIVATE, 'Activate'),
        (DEACTIVATE, 'Deactivate'),
    ]
