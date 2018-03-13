import os, sys
import brass_api.orientdb.brass_orientdb_client
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper

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

    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    config_file = "{0}/../{1}".format(BASE_DIR, options.config)
    if not os.path.exists(config_file):
        print 'Config file does NOT exist.'
        exit()


    try:
        orientDB_helper = BrassOrientDBHelper(database_name=options.database, config_file=config_file)
        '''
        print '********** getParentNode **********'
        print orientDB_helper.get_parent_nodes('#161:0')
        

        print '********** get_connected_nodes **********'
        print orientDB_helper.get_connected_nodes('#109:0', direction='out', maxdepth=1)
        print orientDB_helper.get_connected_nodes('#109:0', maxdepth=3, filterdepth=3)
        '''


        #print orientDB_helper.get_referent_node('#138:0')

        #print orientDB_helper.get_reference_nodes('#245:0')
        #print orientDB_helper.delete_node_by_rid('#327:1')
        #print orientDB_helper.delete_node_by_rid('#327:1')

        #record = orientDB_helper.get_node_by_rid('#325:1')
        #print orientDB_helper.delete_node_by_rid('#325:1')
        #print orientDB_helper.delete_node_by_rid('#1000:0')
        b = orientDB_helper.get_node_by_rid('#71:0')
        a = orientDB_helper.get_node_by_rid('#1000:0')


    except:
        print sys.exc_info()[1]



