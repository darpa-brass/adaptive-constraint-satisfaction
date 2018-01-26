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
    def __init__(self, databaseName, textFile, configFile = 'config.json'):
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

        self.textFile = textFile

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
      Recursively traverses a vertex via the Containment type of edges.
      :argument:
                    record (OrientRecord):      an orientDB record containing data about a vertex
      :return:
      """
      self.printOrientRecord(record)

      #print "select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)
      for v in self.client.command("select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)):
          self.traverse(v)

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



    '''
    orientDB record print function
    '''
    def printOrientRecord(self, record):
        """
        Prints a OrientRecord returned by orientDB query.

        :argument:
                    record (OrientRecord):  an orientDB record containg vertex information
        :return:
        """

        recordStr = []
        for key in record.oRecordData.keys():
            if 'Containment' not in key and 'Reference' not in key:
                recordStr.append('{0}:{1} '.format(key, record.oRecordData[key]))

        print "{0}{1}{2}".format(record._class, createTabString(30-len(record._class)) , str(recordStr))
        self.textFile.write("{0}{1}{2}\n".format(record._class, createTabString(30-len(record._class)) , str(recordStr)))


    def runTraversePrint(self):
        """
        Retrieves the root vertex in the database.
        Calls the example traverse function on the root vertex.

        :argument:
        :return:
        """

        try:
            for v in self.getNodeByProperty('uid', 'MDLRoot-0'):
                self.traverse(v)
            #for v in self.getNodeByClass('MDLRoot'):
            #    print v
        except:
            print "Unexpected error:", sys.exc_info()[0]


    def runModifyRadioLinkSchedule(self):
        """
        Retrieves RadioLink vertices from the database.
        Iterates through each RadioLink vertex and obtains its TxOp children.
        The "StartUSec" and "StopUSec" properties of each TxOp child is incremented by 105.


        :argument:
        :return:
        """

        for v in self.client.command("select @rid, Name from V where @class ='RadioLink'"):
            print '>>>>>>> {0} : {1}'.format(v.oRecordData['rid'], v.oRecordData['Name'])
            self.textFile.write('\n\n>>>>>>> {0} : {1}\n'.format(v.oRecordData['rid'], v.oRecordData['Name']))
            for v_2 in self.client.command("select from (traverse in('Containment') from {0}) where @class='TxOp'".format(v.oRecordData['rid'])):
                print v_2
                self.textFile.write(str(v_2.oRecordData))
                self.textFile.write('\n')

                self.client.command("update {0} set {1}={2}, {3}={4}".
                                    format(v_2._rid, 'StopUSec', int(v_2.StopUSec) + 105, 'StartUSec', int(v_2.StartUSec) + 105))


                #print "update {0} set {1}='{2}', {3}='{4}'".format(v_2._rid, 'StopUSec', int(v_2.StopUSec) + 100, 'StartUSec', int(v_2.StartUSec) + 100)

            self.textFile.write('\n\n Post Modification\n')

            for v_2 in self.client.command("select from (traverse in('Containment') from {0}) where @class='TxOp'".format(v.oRecordData['rid'])):
                print v_2
                self.textFile.write(str(v_2.oRecordData))
                self.textFile.write('\n')


""" Print formatting functions """
def createTabString(numberTabs):
    s = ''
    i = 1
    while i <= numberTabs:
        s += ' '
        i += 1
    return s

""""""


def main(database, remotePlocal):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runTraversePrint().
    Calls runModifyRadioLinkSchedule().
    Closes the orientDB database.

    :argument:
                database (str):     orientDB database name
                remotePlocal (str): remote or local database, not used currently
    :return:
    """
    textFile = open('example_traverse_print_LOG.txt', 'w')
    processor=Processor(database, textFile)

    try:
        processor.openDatabase()

        print '****************             Traverse Print              ****************'
        textFile.write('****************             Traverse Print              ****************\n\n')
        processor.runTraversePrint()

        print '****************       Update RadioLink Schedule         ****************'
        textFile.write('\n\n****************       Update RadioLink Schedule         ****************')
        processor.runModifyRadioLinkSchedule()

        processor.closeDatabase()
    except:
        print "Unexpected error:", sys.exc_info()[0]
        exit(1)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        remotePlocal = sys.argv[2]
    else:
        print('Not enough arguments. The script should be called as following: python example_simple.py myOrientDbDatabase remote')

    main(database, remotePlocal)