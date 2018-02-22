class BrassException(Exception):
    """ Raise for exceptions encountered with brass api and orientdb """

    def __init__(self, message, source=''):
        super(BrassException, self).__init__(message)
        self.message = message
        self.source = source

    def __str__(self):
        return "[ERROR] {0} [SOURCE] {1}\n".format(self.message, self.source)
