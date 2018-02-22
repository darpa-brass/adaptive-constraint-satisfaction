"""

Defines a class called BrassOrientDBClient that wraps
connecting to an orientDB server and database.


Author: Di Yao (di.yao@vanderbilt.edu)

"""

import os
import sys
import json
import pyorient
from brass_exceptions import BrassException

class BrassOrientDBClient(object):
    def __init__(self, databaseName, configFile = 'config.json'):
        data_file= open(configFile, 'r')
        configMap = json.load(data_file)
        data_file.close()

        self._server_username = configMap['server']['username']
        self._server_password = configMap['server']['password']
        self._db_name = databaseName
        self._db_username = None
        self._db_password = None

        if 'database' in configMap:
            if 'username' in configMap['database'] and 'password' in configMap['database']:
                self._db_username = configMap['database']['username']
                self._db_password = configMap['database']['password']

        self._client = pyorient.OrientDB( configMap['server']['address'], configMap['server']['port'] )

        # connect to orion server
        try:
            self._session_id = self._client.connect( self._server_username, self._server_password )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBClient.__init__')


    def openDatabase(self):
        """
        Opens the orientDB database.
        :argument:
        :return:
        """

        try:
            self._client.db_open(self._db_name, self._db_username, self._db_password)
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBClient.openDatabase')

    def closeDatabase(self):
        """
        Closes the orientDB database.
        :argument:
        :return:
        """

        try:
            self._client.db_close()
        except:
            raise BrassOrientDBClient(sys.exc_info()[1], 'BrassOrientDBClient.closeDatabase')


    def runCommand(self, query_str):
        return self._client.command(query_str)


'''
Test Function.
'''
def test(database):
    try:
        orient_client = BrassOrientDBClient(database)
        print "Successfully created Brass OrientDB Query Helper"
    except BrassException as e:
        print e
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python brass_orientdb_client.py myOrientDbDatabase remote')

    test(database)