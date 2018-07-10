"""

example_custom_data_structure.py

This program traverses a database starting from a vertex/vertices via the "Containment" edge.
The data for each vertex is stored in a custom data structure class called MDLNode.
The child vertices are saved inside their parent MDLNode. The resulting hierarchy
should be the exact same as that defined in the imported MDL xml file.

Note: MDLNode is just a simple example that shows a custom data structure class. Users can also
define their custom classes or use an existing graph library like Networkx to store query/traversal
results.


Author: Di Yao (di.yao@vanderbilt.edu)

"""


from lxml import etree
import os
import json
import sys
import pyorient


"""
Custom data structure class.
"""
class MDLNode (object):
    def __init__(self, orientRecord):
        self.orientData = orientRecord
        self.children = []

    def addChildren(self, mdlNode):
        self.children.append( mdlNode )


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
        self.session_id = self.client.connect( self.username, self.password )
        self.db_name = databaseName
        self.db_username = None
        self.db_password = None
        if 'database' in config_data:
            if 'username' in config_data['database'] and 'password' in config_data['database']:
                self.db_username = config_data['database']['username']
                self.db_password = config_data['database']['password']


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

    def traverse(self, record):
        """
        A parent vertex is passed in and a corresponding MDLNode is created for it.
        Recursively traverses the parent vertex via the Containment type of edges.
        Creates a MDLNode for each child vertex and stores them in the parent
        MDLNode's list of children MDLNodes

        :argument:
                    record (OrientRecord):      an orientDB record containing data of the parent
                                                vertex to start traversal from
        :return:
        """

        mdlNode = MDLNode(record)
        #print '{0}                      {1}'.format( record._class, str(record.oRecordData) )

        #print "select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)
        for v in self.client.command("select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)):
            mdlNode.addChildren(self.traverse(v))

        return mdlNode


    '''
      helper query functions
    '''
    def getNodeByClass(self, vertexTypeName):
        """
        Retrieves vertices of a specific type from orientDB database.
        Example:    getNodeByClass("QoSPolicy")
                    getNodeByClass("TestMissions")
                    getNodeByClass("Network")
        :argument:
                    vertexTypeName (str):   a string that specify the vertex class type
        :return:
                    list:                   containg orientDB OrientRecord data
        """

        #print "Select from V where @class='{0}'".format(vertexTypeName)
        return self.client.command("Select from V where @class='{0}'".format(vertexTypeName))


    def getNodeByProperty(self, propertyName, propertyValue):
        """
        Retrieves vertices based on property values orientDB database.
        Example:    getNodeByProperty("uid", "MDLRoot-0"),
                    getNodeByProperty("ID", "TA_RadioComponent1")
                    getNodeByProperty("Name", "TA_RadioComponent")
        :argument:
                    propertyName (str):     "uid", "ID", "Name", "Description", "LowPowerModeEnable", etc
                    propertyValue (str):    "TA_RadioComponent1", "true", "TA_RadioComponent", etc
        :return:
                    list:                   orientDB OrientRecord data
        """

        #print "select from V where {0}='{1}'".format(propertyName, propertyValue)
        return self.client.command("select from V where {0}='{1}'".format(propertyName, propertyValue))



    def runTraverse(self):
        """
        (1) Retrieves the root vertex by the uid property. Calls traverse on
            the root vertex to create a hierarchical MDLNode structure.
        (2) Retrieves all the 'RadioLink' type of vertices. Calls traverse on
            each RadioLink vertex to create a list of hierarchical RadioLink
            MDLNode structures.

        :argument:
        :return:
        """

        try:
            for v in self.getNodeByProperty('uid', 'MDLRoot-0'):
                rootMDLNode = self.traverse(v)

            radioLinkMDLNodes = []
            for v in self.getNodeByClass('RadioLink'):
                radioLinkMDLNodes.append( self.traverse(v) )

        except:
            print("Unexpected error:", sys.exc_info()[0])





def main(database, remotePlocal):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runTraversePrint().
    Closes the orientDB database.

    :argument:
                database (str):     orientDB database name
                remotePlocal (str): remote or local database, not used currently
    :return:
    """

    processor=Processor(database)

    try:
        processor.openDatabase()
        processor.runTraverse()
        processor.closeDatabase()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python example_custom_data_structure.py myOrientDbDatabase remote')

    main(database, remotePlocal)