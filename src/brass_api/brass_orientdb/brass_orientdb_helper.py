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
        if lh == 'rid' or lh == 'class':
            return "@{0}{1}'{2}'".format(lh, op, rh)
        else:
            return "{0}{1}'{2}'".format(lh, op, rh)


    @staticmethod
    # target can be rid or class name or V (for vertex class)
    def select_sql(target, *args):
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
    # target can be rid or class name
    def traverse_sql(target, **kwargs):
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
    # target can be rid or class name
    def update_sql(target, *argv):
        query_sql = ['update']
        query_sql.append(target)

        if len(argv) > 0:
            query_sql.append('set')
            query_sql.append( ', '.join(argv))

        return ' '.join(query_sql)


    def getChildNodes(self, targetNode_rid, edgetype='Containment', maxdepth=1):
        if targetNode_rid is None:
            return None

        #select from (traverse in('Containment') from #109:0 maxdepth 1) where $depth >=1
        print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql(targetNode_rid, direction='in', edgetype=edgetype, maxdepth=maxdepth), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>='))
        #return self._orientdb_client.runCommand(
        # BrassOrientDBHelper.select_sql(
        # BrassOrientDBHelper.traverse_sql(targetNode_rid, direction='in', edgetype=edgetype, maxdepth=maxdepth),
        # BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>=')
        # )
        # )


    def getNodesByType(self, type=None):
        if type is None:
            return None

        # select from TestMissions => where 'TestMissions' is the type
        print BrassOrientDBHelper.select_sql(type)
        #return self._orientdb_client.runCommand(
        # BrassOrientDBHelper.select_sql(type)
        # )


    def getNodeByRID(self, targetNode_rid):
        #select from V where @rid=#93:0
        print BrassOrientDBHelper.select_sql('V', BrassOrientDBHelper.condition_str('rid', targetNode_rid))
        #return self._orientdb_client.runCommand(
        #    BrassOrientDBHelper.select_sql('V', BrassOrientDBHelper.condition_str('rid', targetNode_rid))
        #)


    def getParentNodes(self, targetNode_rid, edgetype='Containment', maxdepth=1):
        if targetNode_rid is None:
            return None

        #select from (traverse out('Containment') from #109:0 maxdepth 1) where $depth >=1
        print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql(targetNode_rid, direction='out', edgetype=edgetype, maxdepth=maxdepth), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>='))
        #return self._orientdb_client.runCommand(
        #  BrassOrientDBHelper.select_sql(
        #      BrassOrientDBHelper.traverse_sql(targetNode_rid, direction='out', edgetype=edgetype, maxdepth=maxdepth), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>=')
        #  )
        #)


    def updateNode(self, targetNode_rid, *args):
        print BrassOrientDBHelper.update_sql(targetNode_rid, *args)
        #return self._orientdb_client.runCommand(
        # BrassOrientDBHelper.update_sql(targetNode_rid, *args)
        # )

    def runQueryCommand(self, sql):
        return self._orientdb_client.runCommand(sql)



if __name__ == "__main__":

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

    #brass_helper.getChildNodes('#161:0')
    print BrassOrientDBHelper.select_sql(
          BrassOrientDBHelper.traverse_sql('#161:0', direction='in', edgetype='Containment', maxdepth=1),
          BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>=')
          )

    #brass_helper.getParentNodes('#161:0')
    print BrassOrientDBHelper.select_sql( BrassOrientDBHelper.traverse_sql('#161:0', direction='out', edgetype='Containment', maxdepth=1), BrassOrientDBHelper.condition_str(lh='$depth', rh=1, op='>='))
