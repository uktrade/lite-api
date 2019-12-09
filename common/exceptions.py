class ApiException(Exception):
    def __init__(self, message, errors):
        self.message = message
        self.errors = errors

    def __str__(self):
        return f'{self.message}: {repr(self.errors)}'
