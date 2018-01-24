"""

example_traverse_print.py

This program contains code to grab the root MDL vertex (MDLRoot) in an orientDB database
then perform a depth-first traversal using "Containment" type of edges from the root vertex.
Each vertex's name and its properties are printed out during the traversal.

TODO: Add traversal of "Reference" type of edges.

Author: Di Yao (di.yao@vanderbilt.edu)

"""


from lxml import etree
import os
import json
import sys
import pyorient

class Processor(object):
    def __init__(self, databaseName, configFile = 'config.json'):
        data_file= open(configFile, 'r')
        config_data = json.load(data_file)
        data_file.close()
        self.username = config_data['server']['username']
        self.password = config_data['server']['password']
        server = config_data['server']['address']
        port =  config_data['server']['port']
        self.client = pyorient.OrientDB(server, port)
        self.session_id = None #self.session_id = self.client.connect( self.username, self.password )

        self.db_name = databaseName
        self.db_username = None
        self.db_password = None
        if 'database' in config_data:
            if 'username' in config_data['database'] and 'password' in config_data['database']:
                self.db_username = config_data['database']['username']
                self.db_password = config_data['database']['password']

    def connectToServer(self):
        self.session_id = self.client.connect( self.username, self.password )

    def openDatabase(self):
        """
        Opens the orientDB database.
        :argument:
        :return:
        """

        self.client.db_open(self.db_name, self.db_username, self.db_password)

    def closeDatabase(self):
        """
        Closes the orientDB database.
        :argument:
        :return:
        """

        self.client.db_close()


def main(database, remotePlocal):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runExample() on the processor object.
    Closes the orientDB database.

    :argument:
                database (str):     orientDB database name
                remotePlocal (str): remote or local database, not used currently
    :return:
    """

    processor=Processor(database)
    try:
        processor.connectToServer()
        print 'Successfully connected to orion server.'
    except:
        print "Unexpected error - connecting to orion server:", sys.exc_info()[1]
        exit(1)

    try:
        processor.openDatabase()
        print 'Successfully connected to database "{0}".'.format(database)
    except:
        print "Unexpected error - connecting to database:", sys.exc_info()[1]
        exit(1)

    processor.closeDatabase()



if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python test_db_connection.py myOrientDbDatabase remote')

    main(database, remotePlocal)