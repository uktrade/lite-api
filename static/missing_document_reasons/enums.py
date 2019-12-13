class GoodMissingDocumentReasons:
    NO_DOCUMENT = "NO_DOCUMENT"
    OFFICIAL_SENSITIVE = "OFFICIAL_SENSITIVE"
    COMMERCIALLY_SENSITIVE = "COMMERCIALLY_SENSITIVE"

    choices = [
        (NO_DOCUMENT, "No document available for the good"),
        (OFFICIAL_SENSITIVE, "Document is above official-sensitive"),
        (COMMERCIALLY_SENSITIVE, "Document is commercially sensitive"),
    ]
