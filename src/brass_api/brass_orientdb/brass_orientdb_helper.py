import os
import sys
import json

from brass_orientdb_client import BrassOrientDBClient
from brass_exceptions import BrassException



class BrassOrientDBHelper(object):
    def __init__(self, orientdb_client=None):
        self._orientdb_client = orientdb_client


    @staticmethod
    def condition_str(lh, rh, op='='):
        '''
        Creates a conditional string for queries in the form of:
        lh op rh


        :param lh: left hand side of the condition
        :param rh: right hand side of the condition
        :param op: logical operator
        :return: string
                    name = 'Clark'
        '''
        if lh == 'rid' or lh == 'class':
            return "@{0}{1}'{2}'".format(lh, op, rh)
        else:
            return "{0}{1}'{2}'".format(lh, op, rh)


    @staticmethod
    def select_sql(target, *args):
        '''
        Creates a select sql string based on the passed in parameters.
        Select queries a database for records (vertices) based on some conditions.

        :param target:  can be rid or class name or V (for vertex class)
        :param args:    list of conditions for the query
        :return:        sql string
        '''
        query_sql = ['select']
        query_sql.append('from')

        if 'traverse' in target:
            query_sql.append('({0})'.format(target))
        else:
            query_sql.append(target)

        if len(args) > 0:
            query_sql.append('where')
            query_sql.append(' and '.join(args))

        return ' '.join(query_sql)

    """
    @staticmethod                                                  
    def form_conditionals(**kwargs):                               
        condition_list = []                                        
        for key, value in kwargs.items():                          
           condition_list.append('@{0}="{1}"'.format(key, value)) 
        return ' and '.join(condition_list)                        
    
    
    @staticmethod
    # target can be rid or class name or V (for vertex class)
    def select(target, **kwargs):
        query_sql = ['select']
        query_sql.append('from')

        if 'traverse' in target:
            query_sql.append('({0})'.format(target))
        else:
            query_sql.append(target)

        if len(kwargs) > 0:
            query_sql.append('where')
            query_sql.append(''.join(BrassOrientDBHelper.form_conditionals(**kwargs)))

        return ' '.join(query_sql)
    """

    @staticmethod
    def traverse_sql(target, **kwargs):
        '''
        Creates a traverse sql string based passed in parameters.
        Traverse retrieves connected records(vertices) crossing relationships(edges).

        :param target:  can be rid or class name
        :param kwargs:  list of traverse conditions
        :return:        sql string
        '''

        query_sql = ['traverse']
        if 'direction' in kwargs:
            if 'edgetype' in kwargs:
                query_sql.append('{0}({1})'.format(kwargs['direction'], kwargs['edgetype']))

        query_sql.append('from')
        query_sql.append(target)

        if 'maxdepth' in kwargs:
            query_sql.append('maxdepth {0}'.format(kwargs['maxdepth']))
        if 'strategy' in kwargs:
            query_sql.append('strategy {0}'.format(kwargs['strategy']))

        return ' '.join(query_sql)


    @staticmethod
    def update_sql(target, *argv):
        '''
        Updates the properties of a database record/vertex.

        :param target:  rid of the record/vertex to update
        :param argv:    List of properties to modify on the record/vertex.
                        OrientDB will create the property if it doesn't already exist.
        :return:        sql string
        '''
        query_sql = ['update']
        query_sql.append(target)

        if len(argv) > 0:
            query_sql.append('set')
            query_sql.append( ', '.join(argv))

        return ' '.join(query_sql)


    def getNodes(self, targetNode_rid, direction='in', edgetype='Containment', maxdepth=1, filterdepth=None, strategy='DEPTH_FIRST'):
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
            print "[WARNING] filterdepth is greater than maxdepth. No results will be returned from query. [SOURCE] BrassOrientDBHelper.getNodes"
            return None

        if filterdepth is None:
            filterdepth_condition = BrassOrientDBHelper.condition_str(lh='$depth', rh=0, op='>')
        else:
            filterdepth_condition = BrassOrientDBHelper.condition_str(lh='$depth', rh=filterdepth)

        #sql command
        #select from (traverse in('Containment') from #109:0 maxdepth 1) where $depth >=1
        #print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql(targetNode_rid, direction=direction, edgetype=edgetype, maxdepth=maxdepth), filterdepth_condition)


        try:
            return self._orientdb_client.runCommand(
                 BrassOrientDBHelper.select_sql(
                 BrassOrientDBHelper.traverse_sql(targetNode_rid, direction=direction, edgetype=edgetype, maxdepth=maxdepth),
                 filterdepth_condition
                 )
             )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.getChildNodes')



    def getNodesByType(self, type=None):
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
        #print BrassOrientDBHelper.select_sql(type)

        try:
            return self._orientdb_client.runCommand(
             BrassOrientDBHelper.select_sql(type)
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.getNodesByType')


    def getNodeByRID(self, targetNode_rid):
        '''
        Retrieves a record/vertex that has the targetNode_rid.

        :param targetNode_rid:  orientdb record id of a record/vertex
        :return:                orientdb record objects
        '''

        # sql command
        #select from V where @rid=#93:0
        #print BrassOrientDBHelper.select_sql('V', BrassOrientDBHelper.condition_str('rid', targetNode_rid))

        try:
            return self._orientdb_client.runCommand(
                BrassOrientDBHelper.select_sql('V', BrassOrientDBHelper.condition_str('rid', targetNode_rid))
            )
        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.getNodeByRID')


    def getChildNodes(self, targetNode_rid, edgetype='Containment'):
        '''
        Retrieve all of targetNode_rid's immediate connected records/vertices (maxdepth=1 and filterdepth = 1)
        via INCOMING edges.

        targetNode_rid <- child

        :param targetNode_rid:  target record/vertex
        :param edgetype:        edge type
        :return:                None or orientdb record objects
        '''
        if targetNode_rid is None:
            return None

        return self.getNodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='in', edgetype=edgetype)


    def getParentNodes(self, targetNode_rid, edgetype='Containment'):
        '''
        Retrieve all of targetNode_rid's immediate connected records/vertices (maxdepth=1 and filterdepth = 1)
        via OUTGOING edges.

        parent <- targetNode_rid

        :param targetNode_rid:  target record/vertex
        :param edgetype:        edge type
        :return:                None or orientdb record objects
        '''

        if targetNode_rid is None:
            return None

        #sql command
        #select from (traverse out('Containment') from #109:0 maxdepth 1) where $depth >=1
        #print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql(targetNode_rid, direction='out', edgetype=edgetype, maxdepth=maxdepth), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>='))

        return self.getNodes(targetNode_rid, maxdepth=1, filterdepth=1, direction='out', edgetype=edgetype)


    def updateNode(self, targetNode_rid, *args):
        '''
        Updates the target record/vertex (targetNode_rid) by the properties and corresponding values
        specified in args.

        :param targetNode_rid:      The record/vertex to update.
        :param args:                List of strings that contains the properties and values to set.
                                    e.g. EncryptionKeyID='gabah gabah', Name='gabah gabah'
        :return:
        '''

        #sql command
        #print BrassOrientDBHelper.update_sql(targetNode_rid, *args)

        try:
            self._orientdb_client.runCommand(
             BrassOrientDBHelper.update_sql(targetNode_rid, *args)
            )
            return True

        except:
            raise BrassException(sys.exc_info()[1], 'BrassOrientDBHelper.updateNode')

    def runQueryCommand(self, sql):
        '''

        :param sql:     The sql string to run
        :return:
        '''
        return self._orientdb_client.runCommand(sql)



if __name__ == "__main__":

    try:
        # Testing 'select'
        conditions = (BrassOrientDBHelper.condition_str('EncryptionKeyID', 'gabah gabah'), BrassOrientDBHelper.condition_str('Name', 'gabah gabah') )
        print BrassOrientDBHelper.select_sql('RadioLink', BrassOrientDBHelper.condition_str('EncryptionKeyID', 'gabah gabah'), BrassOrientDBHelper.condition_str('Name', 'gabah gabah'))
        print BrassOrientDBHelper.select_sql('RadioLink', *conditions)


        # Testing 'traverse'
        print BrassOrientDBHelper.traverse_sql('#161:0', direction='in', edgetype='Containment', maxdepth=3)


        # Testing BrassOrientDBHelper functions by calling
        # the underlying *_sql functions they call

        brass_helper = BrassOrientDBHelper()
        #brass_helper.getNodeByRID('#93:0')
        print BrassOrientDBHelper.select_sql('V', BrassOrientDBHelper.condition_str('rid', '#93:0'))

        #brass_helper.getNodesByType('RadioLink')
        print BrassOrientDBHelper.select_sql('RadioLink')

        #brass_helper.updateNode('#93:0', BrassOrientDBHelper.condition_str('EncryptionKeyID', 'gabah gabah'), BrassOrientDBHelper.condition_str('Name', 'gabah gabah') )
        print BrassOrientDBHelper.update_sql('#93:0', BrassOrientDBHelper.condition_str('EncryptionKeyID', 'gabah gabah'), BrassOrientDBHelper.condition_str('Name', 'gabah gabah') )

        print '********** getChildNodes **********'
        #brass_helper.getChildNodes('#109:0')
        print BrassOrientDBHelper.select_sql(
              BrassOrientDBHelper.traverse_sql('#161:0', direction='in', edgetype='Containment', maxdepth=1),
              BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>=')
              )

        print '********** getParentNode **********'
        #brass_helper.getParentNodes('#161:0')
        #print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql('#161:0', direction='out', edgetype='Containment', maxdepth=1), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>='))

        print '********** getNodes **********'
        #brass_helper.getNodes('#109:0', direction='out', maxdepth=1)
        #brass_helper.getNodes('#109:0', maxdepth=3, filterdepth=3)


    except BrassException as e:
        print sys.exc_info()[1]