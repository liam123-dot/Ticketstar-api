
class FixrApiException(Exception):

    def __init__(self, message, *args):
        self.message = message
        super().__init__(message, *args)

    def __str__(self):
        return "There has been a server issue: " + self.message
