class CaseType:
    APPLICATION = "application"
    CLC_QUERY = "clc_query"
    END_USER_ADVISORY_QUERY = "end_user_advisory_query"
    HMRC_QUERY = "hmrc_query"

    choices = [
        (APPLICATION, "Application"),
        (CLC_QUERY, "CLC Query"),
        (END_USER_ADVISORY_QUERY, "End User Advisory Query"),
        (HMRC_QUERY, "HMRC Query"),
    ]

    @classmethod
    def get_text(cls, choice):
        for key, value in cls.choices:
            if key == choice:
                return value

    @classmethod
    def as_list(cls):
        return [{"value": choice[0], "title": choice[1],} for choice in cls.choices]
