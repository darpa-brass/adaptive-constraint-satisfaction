"""

Module defines a class called BrassOrientDBClient that wraps
connecting to an orientDB server and database.


Author: Di Yao (di.yao@vanderbilt.edu)

"""

import sys
import json
import pyorient
from brass_api.common.exception_class import BrassException

class BrassOrientDBClient(object):
    """
    Wraps the pyorient client and connection to orientdb.

    """
    def __init__(self, database_name, configFile = 'config.json'):
        """

        :param str database_name:       name of orientdb database
        :param str configFile:          name and/or path of config.json to use. config.json contains user credentials
                                        for the orientdb server and database
        """

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
        """
        Connects to the orientdb server.
        Must connect to the server first before opening a database.

        :param:     None
        :return:    None
        :raises BrassException:     source of the exception is set to the name of this function
        """
        try:
            self._session_id = self._client.connect(self._server_username, self._server_password)
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBClient.connect_server')

    def open_database(self, over_write=False):
        """
        Opens the orientDB database.

        :param boolean over_write:          set to True to drop existing database and create a new one,
                                    set to False top open an existing database if it exists
        :return:                    None
        :raises BrassException:     source of the exception is set to the name of this function
        """

        try:
            if over_write:
                if self._client.db_exists(self._db_name):
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

        :param:         None
        :return:        None
        :raises BrassException:     source of the exception is set to the name of this function
        """

        try:
            self._client.db_close()
        except:
            raise BrassOrientDBClient(sys.exc_info()[1], 'BrassOrientDBClient.close_database')

    def drop_database(self):
        """
        Drops a database if it exists.

        :param:     None
        :return:    None
        :raises BrassException:     source of the exception is set to the name of this function
        """

        try:
            if self._client.db_exists(self._db_name):
                self._client.db_drop(self._db_name)

            return True
        except:
            raise BrassOrientDBClient(sys.exc_info()[1], 'BrassOrientDBClient.drop_database')

    def create_database(self):
        """
        Creates a new orientdb database.

        :param:                     None
        :return:                    None
        :raises BrassException:     source of the exception is set to the name of this function
        """
        self._client.db_create(self._db_name, pyorient.DB_TYPE_GRAPH)
        if self._db_password != None and self._db_username != None:
            if self._db_username != 'admin' and self._db_username != 'reader' and self._db_username != 'writer':
                self._client.command(
                    "create user {0} identified by {1} role [writer,reader]".format(self._db_username, self._db_password)
                )

    def run_command(self, query_str):
        """
        Runs sql string commands by calling pyorient client.

        :param str query_str:       sql query command string
        :return:                    results of calling pyorient client with the query string
        """
        return self._client.command(query_str)



'''
Test Function.
'''
def test(database):
    try:
        orient_client = BrassOrientDBClient(database)
        print("Successfully created Brass OrientDB Query Helper")
    except BrassException as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python brass_orientdb_client.py myOrientDbDatabase remote')

    test(database)