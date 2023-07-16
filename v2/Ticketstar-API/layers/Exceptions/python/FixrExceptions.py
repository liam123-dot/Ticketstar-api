
class FixrApiException(Exception):

    def __init__(self, message=None, exception=None, *args):
        self.message = message
        self.exception = exception
        super().__init__(message, *args)

    def __str__(self):
        if self.exception is not None:
            return "There has been a server issue: " + str(self.exception)
        else:
            return "There has been a fixr issue: " + self.message
