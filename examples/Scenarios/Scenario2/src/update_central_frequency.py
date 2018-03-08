"""

update_central_frequency.py

This program contains code to grab the TxOp nodes from an orientDB database
and update each of the TxOp CentralFrequencyHz properties based on a
requirement to change the CentralFrequency

Author: Joseph Hite (joseph.e.hite@vanderbilt.edu)

"""

import sys
import os

sys.path.append('src')
from brass_api.brass_orientdb.brass_orientdb_helper import BrassOrientDBHelper
from brass_api.brass_orientdb.brass_exceptions import BrassException
# from brass_mdl.brass_mdl_exporter import MDLExporter


def reset_orientdb_central_fq(processor):
    TxOp_nodes = processor.get_nodes_by_type('TxOp')
    updated_frequency = 4919500000
    new_fqhz = processor.condition_str('CentralFrequencyHz', str(updated_frequency), '=')
    for node in TxOp_nodes:
        processor.update_node(node._rid, new_fqhz)


def createTabString(number_tabs):
    s = ''
    i = 1
    while i <= number_tabs:
        s += ' '
        i += 1
    return s


'''
orientDB record print function
'''


def printOrientRecord(record):
    """
    Prints a OrientRecord returned by orientDB query.

    :argument:
                record (OrientRecord):  an orientDB record containg vertex information
    :return:
    """

    record_str = []
    for key in record.oRecordData.keys():
        if 'Containment' not in key and 'Reference' not in key:
            record_str.append('{0}:{1} '.format(key, record.oRecordData[key]))

    print "{0}{1}{2}".format(record._class, createTabString(30 - len(record._class)), str(record_str))
    # self.textFile.write("{0}{1}{2}\n".format(record._class, createTabString(30 - len(record._class)), str(recordStr)))


def main(database=None, config_file=None):
    """
    Connects to OrientDB database, discovers the 'TxOp' Children of 'RadioLinks', and modifies the start and end times
    :param (str) database: the name of the OrientDB database
    :param (str) config_file: path to the config file for OrientDB
    :return:
    """
    print '****************       Calling and Restting OrientDB         ****************'

    processor = BrassOrientDBHelper(database, config_file)
    reset_orientdb_central_fq(processor)

    TxOp_nodes = processor.get_nodes_by_type('TxOp')
    # Brass process of applying constraints happens here
    updated_frequency = 4943000000
    new_fqhz = processor.condition_str('CentralFrequencyHz', str(updated_frequency), '=')
    print new_fqhz

    TxOp_nodes = processor.get_nodes_by_type('TxOp')

    for node in TxOp_nodes:
        print node
        print '****************       Updating Node {0}         ****************'.format(node._rid)
        processor.update_node(node._rid, new_fqhz)

    print 'Post Modification'
    TxOp_nodes = processor.get_nodes_by_type('TxOp')
    for node in TxOp_nodes:
        print node

    processor.close_database()


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        database = sys.argv[1]
        config_file = sys.argv[2]
    else:
        sys.exit(
            'Not enough arguments. The script should be called as following: '
            'python {0} <OrientDbDatabase> <config file>'.format(os.path.basename(__file__)))
    main(database, config_file)