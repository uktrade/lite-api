from lite_content.lite_api.static import GoodMissingDocumentReasonsOptions


class GoodMissingDocumentReasons:
    """
    Selection of possible reasons why an exporter may not be expected to upload
    a document for the good through LITE.
    - NO_DOCUMENT: There is no document available for the good they've added
    - OFFICIAL_SENSITIVE: The document is official-sensitive or above
    - COMMERCIALLY_SENSITIVE: The document is commercially sensitive
    In these cases ECJU be contacted to arrange an alternative
    """
    NO_DOCUMENT = "NO_DOCUMENT"
    OFFICIAL_SENSITIVE = "OFFICIAL_SENSITIVE"
    COMMERCIALLY_SENSITIVE = "COMMERCIALLY_SENSITIVE"

    choices = [
        (NO_DOCUMENT, GoodMissingDocumentReasonsOptions.NO_DOCUMENT),
        (OFFICIAL_SENSITIVE, GoodMissingDocumentReasonsOptions.OFFICIAL_SENSITIVE),
        (COMMERCIALLY_SENSITIVE, GoodMissingDocumentReasonsOptions.COMMERCIALLY_SENSITIVE),
    ]
