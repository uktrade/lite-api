class PayloadSchemaException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "Schema exception: {}".format(self.message)


class AuditSchemaException(Exception):
    pass
