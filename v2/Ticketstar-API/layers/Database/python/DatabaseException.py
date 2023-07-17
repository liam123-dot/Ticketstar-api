
class DatabaseException(Exception):

    def __init__(self, parent_exception, *args):
        self.parent_exception = parent_exception
        super().__init__(parent_exception, *args)

    def __str__(self):
        return "There has been a database error: " + str(self.parent_exception)
