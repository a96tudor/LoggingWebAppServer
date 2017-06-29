class Exception:

    def __init__(self, message):
        self.error_message = message

    def __str__(self):
        return str(self.error_message)