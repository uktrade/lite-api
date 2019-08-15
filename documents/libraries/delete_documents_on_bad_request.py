from documents.models import Document


def delete_documents_on_bad_request(data):
    for x in data:
        Document(s3_key=x["s3_key"], name='toDelete').delete_s3()
