class BrassException(Exception):
    """ Raise for exceptions encountered with brass api and orientdb """

    def __init__(self, message, sp_msg=''):
        super(BrassException, self).__init__(message)
        self.message = message
        self.sp_msg = sp_msg
