
class InvalidBodyException(Exception):
    def __init__(self, message, key):
        self.message = message
        self.key = key
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} - {self.key}'


class InvalidQueryStringException(Exception):
    def __init__(self, message, key):
        self.message = message
        self.key = key
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} - {self.key}'
