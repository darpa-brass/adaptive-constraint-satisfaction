import os
import sys
import json

from brass_orientdb_client import BrassOrientDBClient
from brass_exceptions import BrassException
from orientdb_sql import *


class BrassOrientDBHelper(object):
    def __init__(self, database_name=None, config_file=None, orientdb_client=None):
        if orientdb_client is not None:
            self._orientdb_client = orientdb_client
        else:
            if database_name is not None and config_file is not None:
                self._orientdb_client = BrassOrientDBClient(database_name, config_file)
            else:
                self._orientdb_client = None

    def close_database(self):
        self._orientdb_client.close_database()

    def open_database(self, over_write=False):
        self._orientdb_client.open_database(over_write)

    def get_connected_nodes(self, targetNode_rid, direction='in', edgetype='Containment', maxdepth=1, filterdepth=None, strategy='DEPTH_FIRST'):
        '''
        Traverse and retrieve all records/vertices connected to the target record/vertices by the
        egdge/relationship set by "edgetype". Traversal depth is set by "maxdepth".
        Direction of traversal is set by "direction". "filterdepth" restricts the level of records
        to return. Below are some examples

        MDLRoot <- TestMissions <- TestMission <- RadioLinks
                                               <- QoSPolicies


        | targetNode_rid    |   direction   |   maxdepth    |   filterdepth |   returns                          |

        |TestMissions       |   in          |   2           |   >0          |TestMission, RadioLinks, QoSPolicies|
        |TestMissions       |   in          |   2           |   =2          |RadioLinks, QoSPolicies             |
        |TestMissions       |   in          |   2           |   =1          |TestMission                         |
        |RadioLinks         |   out         |   3           |   >0          |TestMission, TestMissions, MDLRoot  |
        |RadioLinks         |   out         |   3           |   =3          |MDLRoot                             |


        :param targetNode_rid:  orientdb record id of the starting record/vertex
        :param direction:       Direction of the edge/relationship
        :param edgetype:        The relationship to use for traversal
        :param maxdepth:        Defines the maximum depth of the traversal
        :param filterdepth:     Defines the depth of the records to return. If none is set, then will return
                                records up to the maxdepth (>0)
        :return:                orientdb record objects
        '''

        if targetNode_rid is None:
            return None

        if filterdepth > maxdepth:
            print "[WARNING] filterdepth is greater than maxdepth. No results will be returned from query. [SOURCE] BrassOrientDBHelper.get_connected_nodes"
            return None

        if filterdepth is None:
            filterdepth_condition = condition_str(lh='$depth', rh=0, op='>')
        else:
            filterdepth_condition = condition_str(lh='$depth', rh=filterdepth)

        #sql command
        #select from (traverse in('Containment') from #109:0 maxdepth 1) where $depth >=1
        #print select_sql(
        #    traverse_sql(targetNode_rid, direction=direction, edgetype=edgetype, maxdepth=maxdepth),
        #    filterdepth_condition
        #)


        try:
            sql_cmd = select_sql(
                 traverse_sql(targetNode_rid, direction=direction, edgetype=edgetype, maxdepth=maxdepth),
                 [filterdepth_condition]
                 )
            print sql_cmd
            return self._orientdb_client.run_command(
                 sql_cmd
             )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_child_nodes')



    def get_nodes_by_type(self, type=None):
        '''
        Retrieves all records/vertices of a specific type.

        :param type:    The type of record/vertex to retrieve
                        e.g. TestMission, RadioLink, QoSPolicy
        :return:        orientdb record objects
        '''

        if type is None:
            return None

        #sql command
        # select from TestMissions => where 'TestMissions' is the type
        #print select_sql(type)

        try:
            sql_cmd = select_sql(type)
            print sql_cmd
            return self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_nodes_by_type')


    def get_node_by_rid(self, targetNode_rid):
        '''
        Retrieves a record/vertex that has the targetNode_rid.

        :param targetNode_rid:  orientdb record id of a record/vertex
        :return:                orientdb record objects
        '''

        # sql command
        #select from V where @rid=#93:0
        #print select_sql('V', condition_str('rid', targetNode_rid))

        try:
            sql_cmd = select_sql('V', [condition_str('rid', targetNode_rid)])
            print sql_cmd
            return self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_node_by_rid')

    def get_nodes_by_properties(self, *property_conditions):
        try:
            sql_cmd = select_sql(property_conditions)
            print sql_cmd
            return self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_node_by_properties')


    def get_child_nodes(self, targetNode_rid, edgetype='Containment'):
        '''
        Retrieve all of targetNode_rid's immediate connected records/vertices (maxdepth=1 and filterdepth = 1)
        via INCOMING edges.

        targetNode_rid <- child

        :param targetNode_rid:  target record/vertex
        :param edgetype:        edge type
        :return:                None or orientdb record objects
        '''

        try:
            if targetNode_rid is None:
                return None

            return self.get_connected_nodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='in', edgetype=edgetype)
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_child_nodes')


    def get_parent_nodes(self, targetNode_rid, edgetype='Containment'):
        '''
        Retrieve all of targetNode_rid's immediate connected records/vertices (maxdepth=1 and filterdepth = 1)
        via OUTGOING edges.

        parent <- targetNode_rid

        :param targetNode_rid:  target record/vertex
        :param edgetype:        edge type
        :return:                None or orientdb record objects
        '''

        try:
            if targetNode_rid is None:
                return None

            #sql command
            #select from (traverse out('Containment') from #109:0 maxdepth 1) where $depth >=1
            #print select_sql( traverse_sql(targetNode_rid, direction='out', edgetype=edgetype, maxdepth=maxdepth), condition_str(lh='$depth', rh=1, op='>='))

            return self.get_connected_nodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='out', edgetype=edgetype)
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_parent_nodes')

    def get_reference_nodes(self, targetNode_rid):
        '''
        Retrieves all the nodes that references targetNode_rid.

        :param targetNode_rid:
        :return:
        '''

        try:
            return self.get_connected_nodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='in', edgetype='Reference')

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_reference_nodes')


    def get_referent_node(self, targetNode_rid=None):
        '''
        Retrieves the node that targetNode_rid refers to.

        :param targetNode_rid:
        :return:
        '''

        try:
            return self.get_connected_nodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='out', edgetype='Reference')

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_referent_node')


    def update_node(self, targetNode_rid, *args):
        '''
        Updates the target record/vertex (targetNode_rid) by the properties and corresponding values
        specified in args.

        :param targetNode_rid:      The record/vertex to update.
        :param args:                List of strings that contains the properties and values to set.
                                    e.g. EncryptionKeyID='gabah gabah', Name='gabah gabah'
        :return:
        '''

        #sql command
        #print update_sql(targetNode_rid, *args)

        try:
            sql_cmd = update_sql(targetNode_rid, *args)
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
            return True

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.update_node')


    def delete_node_by_rid(self, rid=None):
        #delete vertex rid
        try:
            if len(self.get_node_by_rid(rid)) == 0:
                print '[ERROR] Unable to delete node {0} because it does not exist in the database [SOURCE] {1}'.\
                    format(rid, 'BrassOrientDBHelper.delete_node_by_rid')
                return False
            else:
                sql_cmd = delete_v_sql(rid)
                print sql_cmd
                return self._orientdb_client.run_command(
                    sql_cmd
                )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.delete_node_by_rid')


    def delete_nodes_by_rid(self, rid_list):
        status = True
        try:
            # unfortunately the delete vertex command in orientdb doesn't let you delete a list of rids
            for r in rid_list:
                if not self.delete_node_by_rid(r):
                    status = False
            return status

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.delete_nodes_by_rid')

    def set_containment_relationship (self, parent_rid=None, child_rid=None, parent_conditions=[], child_conditions=[]):
        src = None
        dst = None

        if parent_rid is not None:
            dst = parent_rid
        elif len(parent_conditions) > 0:
            dst = select_sql('V', parent_conditions)

        if child_rid is not None:
            src = child_rid
        elif len(child_conditions) > 0:
            src = select_sql('V', child_conditions)

        if src is not None and dst is not None:
            sql_cmd = create_edge_sql('Containment', src, dst)
            print sql_cmd
            return self._orientdb_client.run_command (
                sql_cmd
            )
        else:
            return False

    def set_reference_relationship (self, reference_rid=None, referent_rid=None, reference_condition=[], referent_condition=[]):
        src = None
        dst = None

        if referent_rid is not None:
            dst = referent_rid
        elif len(referent_condition) > 0:
            dst = select_sql('V', referent_condition)

        if reference_rid is not None:
            src = reference_rid
        elif len(reference_condition) > 0:
            src = select_sql('V', reference_condition)

        if src is not None and dst is not None:
            sql_cmd = create_edge_sql('Reference', src, dst)
            print sql_cmd
            return self._orientdb_client.run_command (
                sql_cmd
            )
        else:
            return ''

    def remove_parent_child_relationship(self, parent_rid=None, child_rid=None, parent_condition=[], child_condition=[]):
        src = None
        dst = None

        if parent_rid is not None:
            dst = parent_rid
        elif len(parent_condition) > 0:
            dst = select_sql('V', parent_condition)

        if child_rid is not None:
            src = child_rid
        elif len(child_condition) > 0:
            dst = select_sql('V', child_condition)


        if src is not None and dst is not None:
            sql_cmd = delete_e_sql('Containment', src, dst)
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
        else:
            return ''

    def remove_reference_relationship(self, reference_rid=None, referent_rid=None, reference_condition=[], referent_condition=[]):
        src = None
        dst = None

        if referent_rid is not None:
            dst = referent_rid
        elif len(referent_condition) > 0:
            dst = select_sql('V',referent_condition)

        if reference_rid is not None:
            src = reference_rid
        elif len(reference_condition) > 0:
            dst = select_sql('V', reference_condition)

        if src is not None and dst is not None:
            sql_cmd = delete_e_sql('Reference', src, dst)
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
        else:
            return ''


    def create_node_class(self, name):
        try:
            sql_cmd = create_class_sql(name, 'V')
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.create_node_class')


    def create_edge_class(self, name):
        try:
            sql_cmd = create_class_sql(name, 'E')
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.create_edge_class')

    def create_node(self, type, properties={}):
        try:
            sql_cmd = insert_sql(type, **properties)
            print sql_cmd
            self._orientdb_client.run_command(
                sql_cmd
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.create_node')



    def run_query(self, sql):
        '''

        :param sql:     The sql string to run
        :return:
        '''
        return self._orientdb_client.run_command(sql)




