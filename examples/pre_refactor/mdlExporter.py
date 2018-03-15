"""
mdlExporter.py

Traverses an orientDB database and exports the information
to an MDL xml file.

Note:   Only "Containment" type of edges are used in the exporter.
        The "Reference" edge is not needed since the XML needs
        IDREF attribute that is already a property of a vertex
        (RadioLinkRef, SourceRadioRef, DestinationGroupRadioRef vertices).

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
        self.session_id = self.client.connect( self.username, self.password )
        self.db_name = databaseName
        self.db_username = None
        self.db_password = None
        if 'database' in config_data:
            if 'username' in config_data['database'] and 'password' in config_data['database']:
                self.db_username = config_data['database']['username']
                self.db_password = config_data['database']['password']

        self.xmlFile = open(databaseName +'_Exported_MDL.xml', 'w')
        self.property2Skip = ['uid', 'ID', 'IDREF', 'in_Containment', 'out_Containment', 'in_Reference', 'out_Reference']


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

    def printNode(self, record, numberTabs):
        """
        Calls printOrientRecord() on a vertex to convert its data
        to xml and write to a file.
        Recursively calls printNode on child vertices via "Containment" edge.
        Closing xml tag is written in this function because closing tag needs
        to come after all child xml elments have been written to file.

        :argument:
                    record (OrientRecord):  an orientDB record containing data about a vertex
                    numberTabs (int):       number of tabs to indent before xml text
        :return:
        """

        self.printOrientRecord(record, numberTabs)

        #print "select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)
        for v in self.client.command("select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)):
            self.printNode(v, numberTabs+1)

        # write out closing xml tag
        self.xmlFile.write('{0}</{1}>\n'.format(self.createTabString(numberTabs), record._class))


    """
    helper query functions
    """
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
    """"""


    """
    orientDB record print function
    """
    def printOrientRecord(self, record, numberTabs):
        """
        Serializes OrientRecord to xml for a vertex and writes to the xml file.
        Serialization involves traversing through a vertex's properties.
        Opening xml tag is written in this function because "ID" and "IDREF"
        properties need to be written out as xml attributes and not as xml tag text.


        :argument:
                    record (OrientRecord):  an orientDB record containing data about a vertex
                    numberTabs (int):       number of tabs to indent before xml text
        :return:

        """

        self.xmlFile.write( "{0}<{1}".format(self.createTabString(numberTabs), record._class) )

        if 'ID' in record.oRecordData.keys():
            self.xmlFile.write(' {0}="{1}"'.format('ID', record.oRecordData['ID']) )
        elif 'IDREF' in record.oRecordData.keys():
            self.xmlFile.write(' {0}="{1}"'.format('IDREF', record.oRecordData['IDREF']) )

        self.xmlFile.write( ">\n" )

        for key in record.oRecordData.keys():
            if key not in self.property2Skip:
                self.xmlFile.write( '{0}<{1}>{2}</{1}>\n'.format( self.createTabString(numberTabs+1), key, record.oRecordData[key] ) )


    """ Print formatting functions """
    def createTabString(self, numberTabs):
        s = ''
        i = 1
        while i <= numberTabs:
            s += '\t'
            i += 1
        return s

    """"""

    def exportToMDL(self):
        """
        Retrieves the root vertex in the database.
        Calls the printNode function on the root vertex to
        traverse and print xml of child vertices to a file.

        :argument:
        :return:
        """

        try:
          for v in self.getNodeByProperty('uid', 'MDLRoot-0'):
              self.printNode(v, 0)
          #for v in self.getNodeByClass('MDLRoot'):
          #    print v
        except:
          print "Unexpected error:", sys.exc_info()[0]



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

    try:
        processor=Processor(database)
        processor.openDatabase()
        processor.exportToMDL()
        processor.closeDatabase()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python mdlExporter.py myOrientDbDatabase remote')

    main(database, remotePlocal)