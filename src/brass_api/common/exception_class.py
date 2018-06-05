"""

Module contains exception class thrown by brass api classes.
"message" is the error message and "source" is the class and function that
throws the exception.

Author: Di Yao (di.yao@vanderbilt.edu)
"""

class BrassException(Exception):
    """ Raise for exceptions encountered with brass api and orientdb """

    def __init__(self, message, source=''):
        """
        Constructor

        :param str message:     exception message
        :param str source:      which function threw the exception
        """
        super(BrassException, self).__init__(message)
        self.message = message
        self.source = source

    def __str__(self):
        return "[EXCEPTION] {0} [SOURCE] {1}\n".format(self.message, self.source)
