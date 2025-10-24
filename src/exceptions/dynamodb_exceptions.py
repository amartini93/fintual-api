class DynamoDBItemNotFoundException(Exception):

    def __init__(self, error):
        self.message = error
        self.error_code = 404
        super().__init__(self.message)

    def get_error_code(self):
        return self.error_code

    def __str__(self):
        return self.message


class DynamoDBInvalidResponseException(Exception):

    def __init__(self, error):
        self.message = error
        self.error_code = 500
        super().__init__(self.message)

    def get_error_code(self):
        return self.error_code

    def __str__(self):
        return self.message


class InternalServerException(Exception):

    def __init__(self, error: str = None):
        self.message = error if error else "Internal server error"
        self.error_code = 500
        super().__init__(self.message)

    def get_error_code(self):
        return self.error_code

    def __str__(self):
        return self.message
