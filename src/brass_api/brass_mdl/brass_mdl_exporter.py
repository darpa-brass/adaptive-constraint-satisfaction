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



import json
import sys
import pyorient
#from brass_api.brass_orientdb.brass_orientdb_client import *
from brass_api.brass_orientdb.brass_exceptions import *
from brass_api.brass_orientdb.brass_orientdb_helper import *
import brass_print_util


class MDLExporter(object):
    def __init__(self, databaseName, configFile = 'config.json'):
        #self.orientDB_helper = BrassOrientDBHelper( orientdb_client=BrassOrientDBClient(databaseName, configFile) )
        self.orientDB_helper = BrassOrientDBHelper(database_name=databaseName, config_file=configFile)
        self.xmlFile = open(databaseName +'_Exported_MDL.xml', 'w')

    def print_node(self, record, numberTabs=0):
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

        self.xmlFile.write(
            brass_print_util.orient_record_to_xml(record, numberTabs)
        )

        #print "select from (traverse in ('Containment') from {0} while $depth < 2) where @rid != {0}".format(record._rid)
        for v in self.orientDB_helper.get_child_nodes(record._rid):
            self.print_node(v, numberTabs + 1)

        # write out closing xml tag
        self.xmlFile.write(
            '{0}</{1}>\n'.format(
                brass_print_util.create_tab_string(numberTabs),
                record._class
            )
        )


    def export_to_mdl(self):
        """
        Retrieves the root vertex in the database.
        Calls the printNode function on the root vertex to
        traverse and print xml of child vertices to a file.

        :argument:
        :return:
        """

        try:
            # select the root record/vertex that is type MDLRoot
            for v in self.orientDB_helper.get_nodes_by_type('MDLRoot'):
                self.print_node(v)

        except:
          print "Unexpected error:", sys.exc_info()[1]



def main(database, config, remotePlocal=None):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runExample() on the processor object.
    Closes the orientDB database.

    :argument:
                database (str):     orientDB database name
                remotePlocal (str): remote or local database, not used currently
    :return:
    """

    import os
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    config_file = "{0}/../{1}".format(BASE_DIR, config)
    if not os.path.exists(config_file):
        print 'Config file does NOT exist.'
        return

    try:
        processor=MDLExporter(database, config_file)
        processor.export_to_mdl()
    except:
        print "Unexpected error:", sys.exc_info()[1]
        exit(1)
    finally:
        processor.orientDB_helper.close_database()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] arg1 arg2")

    parser.add_option("-d", "--database",
                      help="Name of database to open",
                      default=False)

    parser.add_option("-c", "--config",
                      help="Name and path to config.json",
                      default=False)

    parser.add_option("-m", "--mode",
                      help="Mode to use in connecting to the database {plocal, remote}",
                      default=False)

    (options, args) = parser.parse_args()

    main(options.database, options.config, options.mode)
    
