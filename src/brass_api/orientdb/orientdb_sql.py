"""

Module contains functions that create sql command strings for orientdb.

Author: Di Yao (di.yao@vanderbilt.edu)

"""


def condition_str(lh, rh, op='='):
    '''
    Creates a conditional string for queries in the form of: lh op 'rh'

    name = 'a test mission'
    time > '20000'


    :param str lh: left hand side of the condition
    :param str rh: right hand side of the condition
    :param str op: logical operator
    :return:        conditional string in the form of name = 'Clark'
    '''
    if lh == 'rid' or lh == 'class':
        return "@{0}{1}'{2}'".format(lh, op, rh)
    else:
        return "{0}{1}'{2}'".format(lh, op, rh)


def select_sql(target_name, conditions=[], data_to_extract=[]):
    '''
    Creates a select sql string based on the passed in parameters.
    Select queries a database for records (vertices) based on some conditions.

    :param str target_name:              can be rid or class name or V (for vertex class)
    :param list conditions:         list of conditions for the query
    :param list data_to_extract:    list of data fields to extract
    :return:                        sql select command string
    '''
    query_sql = ['select']

    if len(data_to_extract) > 0:
        query_sql.append(','.join(data_to_extract))

    query_sql.append('from')

    if 'traverse' in target_name:
        query_sql.append('({0})'.format(target_name))
    else:
        query_sql.append(target_name)

    if len(conditions) > 0:
        query_sql.append('where')
        query_sql.append(' and '.join(conditions))

    return ' '.join(query_sql)


"""                                               
def form_conditionals(**kwargs):                               
    condition_list = []                                        
    for key, value in kwargs.items():                          
       condition_list.append('@{0}="{1}"'.format(key, value)) 
    return ' and '.join(condition_list)                        


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


def traverse_sql(target_name, **kwargs):
    '''
    Creates a traverse sql string based passed in parameters.
    Traverse retrieves connected records(vertices) crossing relationships(edges).

    :param str target_name:  can be rid or class name
    :param kwargs:  list of traverse conditions
    :return:        sql traverse command string
    '''

    query_sql = ['traverse']
    if 'direction' in kwargs:
        if 'edgetype' in kwargs:
            query_sql.append("{0}('{1}')".format(kwargs['direction'], kwargs['edgetype']))

    query_sql.append('from')
    query_sql.append(target_name)

    if 'maxdepth' in kwargs:
        query_sql.append('maxdepth {0}'.format(kwargs['maxdepth']))
    if 'strategy' in kwargs:
        query_sql.append('strategy {0}'.format(kwargs['strategy']))

    return ' '.join(query_sql)


def update_sql(target_name, *argv):
    '''
    Updates the properties of a database record/vertex.

    :param str target_name:  rid of the record/vertex to update
    :param list argv:    List of properties to modify on the record/vertex.
                    OrientDB will create the property if it doesn't already exist.
    :return:        sql update command string

    '''
    query_sql = ['update']
    query_sql.append(target_name)

    if len(argv) > 0:
        query_sql.append('set')
        query_sql.append(', '.join(argv))

    return ' '.join(query_sql)


def delete_v_sql(rid):
    """
    Forms a delete node with rid sql command.

    :param str rid:         rid of node to delete
    :return:                sql delete vertex command string
    """
    query_sql = ['delete', 'vertex', rid]
    return ' '.join(query_sql)

def delete_e_sql(target_name, src, dst):
    """
    Forms a delete edge sql command between src and dst nodes.

    :param str target_name:        type of edge to delete
    :param str src:         src of the edge - can be rid or a search string
    :param str dst:         dst of the edge - can be rid or a search string
    :return:                sql delete edge command string
    """
    if not src.startswith('#'):
        src = ('(' + src + ')')

    if not dst.startswith('#'):
        dst = ('(' + dst + ')')

    query_sql = ['delete', 'edge', 'from', src, 'to', dst, 'where', "@class = '" + target_name + "'"]
    return ' '.join(query_sql)

def create_vertex_sql(target_name, **properties):
    """
    Returns a sql command to create a new node with properties and values specified by "properties".

    :param str target_name:                        type of node to create
    :param dictionary properties:           properties and values of the node
    :return:                                sql create vertex command string
    """
    query_sql = ['create', 'vertex', target_name]

    if len(properties) > 0:
        query_sql.append('set')

    properties_l = []
    for k in properties.keys():
        properties_l.append( condition_str(k, properties[k]) )

    query_sql.append( ','.join(properties_l) )
    return ' '.join(query_sql)



def create_edge_sql(target_name, src, dst):
    """
    Creates a new edge of type between src and dst nodes.

    :param str target_name:        type of edge of create
    :param str src:         src of the edge - can be rid or a search string
    :param str dst:         dst of the edge - can be rid or a search string
    :return:                sql create edge command string
    """
    if not src.startswith('#'):
        src = ('(' + src + ')')

    if not dst.startswith('#'):
        dst = ('(' + dst + ')')

    query_sql = ['create', 'edge', target_name, 'from', src, 'to', dst]
    return ' '.join(query_sql)



def create_class_sql(target_name, superclass='V', cluster_size=1):
    """
    Forms a create vertex or an edge class sql command.

    :param str target_name:                name of the class ("MDLRoot", "RadioLink", etc)
    :param str superclass:          either V or E
    :param int cluster_size:        the cluster size for the new class
    :return:                        sql create class command string
    """
    query_sql = ['create', 'class', target_name, 'extends', superclass, 'clusters', str(cluster_size)]
    return ' '.join(query_sql)


def insert_sql(target_name, **properties):
    """
    Creates a new vertex or edge of "type" with properties specified by "properties".

    :param str target_name:                type of vertex node or edge to create (MDLRoot, RadioLink, etc)
    :param dictionary properties:   properties and values to set for the new vertex node or edge
    :return:                        sql insert command string
    """

    query_sql = ['insert into', target_name]

    columns=''
    values=''
    for k in properties.keys():
        if columns != '':
            columns += ' ,'
        if values != '':
            values += ' ,'
        columns += k
        values += "'" + str(properties[k]) + "'"
    query_sql.append('(' + columns + ')')
    query_sql.append('values')
    query_sql.append( '(' + values + ')')

    return ' '.join(query_sql)


if __name__ == "__main__":
    # Testing 'select'
    conditions = {condition_str('EncryptionKeyID', 'gabah gabah'), condition_str('Name', 'gabah gabah')}
    print(select_sql('RadioLink', {condition_str(lh='EncryptionKeyID', rh='gabah gabah'), condition_str(lh='Name', rh='gabah gabah')}))
    print(select_sql('RadioLink', conditions))
    print(select_sql('V', {condition_str('rid', '#93:0')}))
    print(select_sql('RadioLink'))
    print(select_sql(
        traverse_sql('#161:0', direction='in', edgetype='Containment', maxdepth=1),
        {condition_str(lh='$depth', rh=1, op='>=')}
    ))


    # Testing 'traverse'
    print(traverse_sql('#161:0', direction='in', edgetype='Containment', maxdepth=3))

    # Testing 'update'
    print(update_sql('#93:0', condition_str('EncryptionKeyID', 'gabah gabah'), condition_str('Name', 'gabah gabah')))

    # Testing 'create'
    print(create_class_sql('myVertex'))
    print(create_class_sql('myEdge', superclass='E'))
    print(create_edge_sql('myEdge', '#30:0', '#28:0'))
    print(create_edge_sql('myEdge', select_sql('V', {condition_str('uid', 'dkakhdfdakdafd')}), '#28:0'))
    print(create_vertex_sql('myVertex', a='b', c=2, g='1kdfdk', h=0.100))

    # Testing 'delete'
    print(delete_e_sql('myVertex', '#5:0', '#6:0'))
    print(delete_v_sql('#35:0'))

    # Testing 'insert'
    print(insert_sql('myVertex', a='b', c=2, g='1kdfdk', h=0.100))
    properties = {'a':'b', 'c':2, 'g':'1kdfdk', 'h':0.100}
    print(insert_sql('myVertex', **properties))
