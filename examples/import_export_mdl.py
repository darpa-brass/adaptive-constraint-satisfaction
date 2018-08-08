"""

example_traverse_print.py

This program contains code to grab the root MDL vertex (MDLRoot) in an orientDB database
then perform a depth-first traversal using "Containment" type of edges from the root vertex.
Each vertex's name and its properties are printed out during the traversal.

Author: Joseph Hite (joseph.e.hite@vanderbilt.edu)

"""

import sys
sys.path.append('src')
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper
from brass_api.common.exception_class import BrassException
from brass_api.mdl.mdl_exporter import MDLExporter
from brass_api.mdl.mdl_importer import MDLImporter





def main(database=None, config_file=None, mdl_file=None):
    """
    Connects to OrientDB database, discovers the 'TxOp' Children of 'RadioLinks', and modifies the start and end times
    :param (str) database: the name of the OrientDB database
    :param (str) config_file: path to the config file for OrientDB
    :return:
    """
    print('****************       Importing {0}          ****************'.format(mdl_file))
    importer = MDLImporter(databaseName=database, configFile=config_file, mdlFile=mdl_file)
    importer.import_mdl()
    importer.orientDB_helper.close_database()

    exporter = MDLExporter(databaseName=database, configFile=config_file)
    exporter.export_to_mdl()
    exporter.orientDB_helper.close_database()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        config_file = sys.argv[2]
        mdl_file = sys.argv[3]
    else:
        sys.exit(
            'Not enough arguments. The script should be called as following: python example_simple.py myOrientDbDatabase remote')
    main(database, config_file, mdl_file)