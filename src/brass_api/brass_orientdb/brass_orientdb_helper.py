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
            return self._orientdb_client.run_command(
                 select_sql(
                 traverse_sql(targetNode_rid, direction=direction, edgetype=edgetype, maxdepth=maxdepth),
                 filterdepth_condition
                 )
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
            return self._orientdb_client.run_command(
             select_sql(type)
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
            return self._orientdb_client.run_command(
                select_sql('V', condition_str('rid', targetNode_rid))
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.get_node_by_rid')


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
            self._orientdb_client.run_command(
             update_sql(targetNode_rid, *args)
            )
            return True

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.update_node')


    #def create_node(self, type, **properties):
    #    try:
    #        #self._orientdb_client.run_command(create_v_sql(type, properties))
    #    except:
    #        raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.add_node')



    def delete_node_by_rid(self, rid=None):
        #delete vertex rid
        try:
            if len(self.get_node_by_rid(rid)) == 0:
                print '[ERROR] Unable to delete node {0} because it does not exist in the database [SOURCE] {1}'.\
                    format(rid, 'BrassOrientDBHelper.delete_node_by_rid')
                return False
            else:
                return self._orientdb_client.run_command( delete_v_sql(rid) )
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

    def set_containment_relationship (self, parent_rid, child_rid, parent_query=None, child_query=None):
        src = None
        dst = None

        if parent_rid is not None:
            dst = parent_rid
        else:
            dst = parent_query

        if child_rid is not None:
            src = child_rid
        else:
            src = child_query

        if src is not None and dst is not None:
            return self._orientdb_client.run_command ( create_edge_sql('Containment', src, dst) )
        else:
            return False

    def set_reference_relationship (self, reference_rid, referent_rid, reference_query=None, referent_query=None):
        src = None
        dst = None

        if referent_rid is not None:
            dst = referent_rid
        else:
            dst = referent_query

        if reference_rid is not None:
            src = reference_rid
        else:
            src = reference_query

        if src is not None and dst is not None:
            return self._orientdb_client.run_command ( create_edge_sql('Reference', src, dst) )
        else:
            return False

    def remove_parent_child_relationship(parent_rid, child_rid, parent_query=None, child_query=None):
        src = None
        dst = None

        if src is not None and dst is not None:
            delete_e_sql('Containment', src, dst)
        else:
            return False

    def remove_reference_relationship(reference_rid, referent_rid, reference_query=None, referent_query=None):
        src = None
        dst = None

        if src is not None and dst is not None:
            delete_e_sql('Reference', src, dst)
        else:
            return False


    def create_node_class(self, name):
        create_class_sql(name, 'V')


    def create_edge_class(self, name):
        create_class_sql(name, 'E')


    def run_query(self, sql):
        '''

        :param sql:     The sql string to run
        :return:
        '''
        return self._orientdb_client.run_command(sql)




