"""

Defines a class called BrassOrientDBClient that wraps
connecting to an orientDB server and database.


Author: Di Yao (di.yao@vanderbilt.edu)

"""

import os
import sys
import json
import pyorient
from pyorient import PyOrientException
from brass_exceptions import BrassException

class BrassOrientDBClient(object):
    def __init__(self, database_name, configFile = 'config.json'):
        data_file= open(configFile, 'r')
        configMap = json.load(data_file)
        data_file.close()

        self._server_username = configMap['server']['username']
        self._server_password = configMap['server']['password']
        self._db_name = database_name
        self._db_username = None
        self._db_password = None

        if 'database' in configMap:
            if 'username' in configMap['database'] and 'password' in configMap['database']:
                self._db_username = configMap['database']['username']
                self._db_password = configMap['database']['password']

        self._client = pyorient.OrientDB( configMap['server']['address'], configMap['server']['port'] )

        # connect to orion server
        self.connect_server()


    def connect_server(self):
        try:
            self._session_id = self._client.connect(self._server_username, self._server_password)
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBClient.connect_server')

    def open_database(self, over_write=False):
        """
        Opens the orientDB database.
        :argument:
        :return:
        """

        try:
            if over_write:
                self.drop_database()
                self.create_database()
            else:
                if self._client.db_exists(self._db_name):
                    self._client.db_open(self._db_name, self._db_username, self._db_password)
                else:
                    self.create_database()
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBClient.open_database')


    def close_database(self):
        """
        Closes the orientDB database.
        :argument:
        :return:
        """

        try:
            self._client.db_close()
        except:
            raise BrassOrientDBClient(sys.exc_info()[1], 'BrassOrientDBClient.close_database')

    def drop_database(self):
        """
        Drops a database if it exists.

        :return:
        """

        try:
            if self._client.db_exists(self._db_name):
                self._client.db_drop(self._db_name)

            return True
        except:
            raise BrassOrientDBClient(sys.exc_info()[1], 'BrassOrientDBClient.drop_database')

    def create_database(self):
        self._client.db_create(self._db_name, pyorient.DB_TYPE_GRAPH)
        if self._db_password != None and self._db_username != None:
            self._client.command(
                "create user {0} identified by {1} role [writer,reader]".format(self._db_username, self._db_password)
            )

    def run_command(self, query_str):
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