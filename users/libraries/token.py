import json
from base64 import b64decode, b64encode


class Token:
    @staticmethod
    def decode_to_json(encoded):
        decoded = b64decode(bytes(encoded, "utf-8")).decode("utf-8").replace("'", '"')
        return json.loads(decoded)

    @staticmethod
    def encode_json(payload):
        return b64encode(bytes(str(payload), "utf-8")).decode("utf-8")
