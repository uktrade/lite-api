from lite_content.lite_api.static import GoodMissingDocumentReasonsOptions


class GoodMissingDocumentReasons:
    NO_DOCUMENT = "NO_DOCUMENT"
    OFFICIAL_SENSITIVE = "OFFICIAL_SENSITIVE"
    COMMERCIALLY_SENSITIVE = "COMMERCIALLY_SENSITIVE"

    choices = [
        (NO_DOCUMENT, GoodMissingDocumentReasonsOptions.NO_DOCUMENT),
        (OFFICIAL_SENSITIVE, GoodMissingDocumentReasonsOptions.OFFICIAL_SENSITIVE),
        (COMMERCIALLY_SENSITIVE, GoodMissingDocumentReasonsOptions.COMMERCIALLY_SENSITIVE),
    ]
