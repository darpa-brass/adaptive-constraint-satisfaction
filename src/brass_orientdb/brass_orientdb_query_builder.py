import os
import sys
import json

from brass_orientdb_client import BrassOrientDBClient


def form_conditionals(**kwargs):
    condition_list = []
    for key, value in kwargs.items():
        condition_list.append( '{0}="{1}"'.format(key, value) )
    return ' and '.join(condition_list)


# target can be rid or class name
def select(target, **kwargs):
    query_sql = ['select']
    query_sql.append('from')

    if 'traverse' in target:
        query_sql.append('({0})'.format(target))
    else:
        query_sql.append(target)

    if len(kwargs) > 0:
        query_sql.append('where')
        query_sql.append( form_conditionals(**kwargs) )

    return ' '.join(query_sql)


# target can be rid or class name
def traverse(target, **kwargs):
    query_sql = ['traverse']

    if 'direction' in kwargs:
        if 'edge_type' in kwargs:
            query_sql.append( '{0}({1})'.format(kwargs['direction'],kwargs['edge_type']) )

    query_sql.append('from')
    query_sql.append(target)

    if 'max_depth' in kwargs:
        query_sql.append('maxdepth {0}'.format(kwargs['maxdepth']))
    if 'strategy' in kwargs:
        query_sql.append('strategy {0}'.format(kwargs['strategy']))

    return ' '.join(query_sql)


# target can be rid or class name
def update(target, **kwargs):
    query_sql = ['update']
    query_sql.append(target)

    if len(kwargs) > 0:
        query_sql.append('set')
        query_sql.append( form_conditionals(**kwargs) )

    return ' '.join(query_sql)


if __name__ == "__main__":
    conditions = {'name':'TestMission1', 'id':1}

    print select('TestMission', **conditions)
    print select('TestMission')

    print update('TestMission', **conditions)

    traverse_conditions = {'direction':'out', 'edge_type':'Friends'}
    print traverse('#25:0', **traverse_conditions)


    print select(traverse('#25:0', **traverse_conditions), **conditions)