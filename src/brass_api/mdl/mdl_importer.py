"""

Module contains an importer class that parses an MDL xml file and
creates an orientdb database from it.

Author: Di Yao (di.yao@vanderbilt.edu)

"""

import sys, os, shutil
import lxml
import pyorient
from lxml import etree
from xml_util import *
from brass_api.orientdb.orientdb_helper import BrassOrientDBHelper
from brass_api.orientdb.orientdb_sql import condition_str, select_sql


class MDLImporter(object):
    """
    Class responsible for importing mdl xml files into an orientdb database.
    :param      databaseName:
    :param      mdlFile:
    :param      configFile:
    """
    def __init__(self, databaseName, mdlFile, configFile = 'config.json'):

        self.loadrObject = []
        self.uniqueIdentifiers = {}

        self.orientDB_helper = BrassOrientDBHelper(database_name=databaseName, config_file=configFile)
        self.mdlFile = mdlFile
        self.orientDB_helper.open_database(over_write=False)


    def import_mdl(self):
        """
        Main function called to start the import process.
        A temporary copy of the mdl file is saved with attributes removed from the
        <MDLRoot>.
        The temporary mdl file is then valided against mdl schema and parsed.
        Lastly the temporary mdl file is removed.
        :param:
        :return:
        """
        orient_mdl_file = self.mdlFile + '.orientdb'
        shutil.copy2(self.mdlFile, orient_mdl_file)

        self._mdl_schema = remove_mdl_root_tag_attr(orient_mdl_file)

        validate_mdl(self.mdlFile, self._mdl_schema)

        self.parseXML(orient_mdl_file)

        os.remove(orient_mdl_file)

    def parseXML(self, xmlFile):
        """
        Parses passed in xmlFile and calls functions to create nodes and edges in
        orientdb.

        :param str xmlFile:         xml file to import
        :return:
        :raises BrassException:     catches any parsing error and rethrows as BrassException

        """
        # this is a stack we maintain when traversing the xml tree
        attribute_stack = []

        # after we decide something should be a vertex we add it to the vertex list
        vertices = []

        # a list of the vertices names (which could also be derived from vertices)
        #     so we know what OrientDB classes to create
        verticesNames = []

        # the two types of edges
        containmentEdges = []
        referenceEdges = []

        for event, elem in etree.iterparse(xmlFile, events=('start', 'end')):
            # at the beginning, add everything on the stack
            # the event can contain attributes eg:<QoSPolicy ID="GR1_to_TA1_MissionSLP"> (in which case we want to get them)
            #      or not <TestMission>
            if event == 'start':
                item = {}
                item[elem.tag] = elem.text if elem.text else ''
                for el in elem.attrib.keys():
                    item[el] = elem.attrib[el]
                attribute_stack.append({elem.tag: item})

                # the hardest part is at the end
                # we are trying to decide if the event closed out a vertex or something that should be an attribute of a vertex
                # eg:
                ''' <TestMission>
                       <Name>Test Mission 1</Name>
                       <Description>Test Mission 1: Frequency change</Description>
                       <TmNSCompleteness>true</TmNSCompleteness>
                       <TmNSCompletenessDescription>Complete</TmNSCompletenessDescription>
                    </TestMission>
                '''
                # in this example the algoritm should detect that TestMission should be a vertex
                # and Name, Description, TmNSCompleteness, TmNSCompletenessDescription should be attributes of TestMission
            elif event == 'end':

                # if the last attribute on the stack contains more than one thing, it's a vertex
                if len(attribute_stack[-1][attribute_stack[-1].keys()[0]].keys()) > 1:
                    try:
                        attribute_stack[-1][attribute_stack[-1].keys()[0]].pop(attribute_stack[-1].keys()[0])
                    except:
                        pass

                    a = attribute_stack.pop()
                    # if it doesn't have a unique identifier, will assign and also assign uid for the parent
                    if self.uidAlreadyAssigned(a) == 0:
                        a[a.keys()[0]]['uid'] = self.assignUniqueId(a.keys()[0])
                    try:
                        if self.uidAlreadyAssigned(attribute_stack[-1]) == 0:
                            attribute_stack[-1][attribute_stack[-1].keys()[0]]['uid'] = self.assignUniqueId(
                                attribute_stack[-1].keys()[0])
                    except:
                        pass

                    # adding to the vertices list
                    vertices.append(a)
                    verticesNames.append(a.keys()[0])
                    try:

                        # creating a containment edge
                        containmentEdges.append(
                            [a[a.keys()[0]]['uid'], attribute_stack[-1][attribute_stack[-1].keys()[0]]['uid']])
                    except:
                        pass

                    try:
                        if len(attribute_stack) > 1:
                            if self.uidAlreadyAssigned(attribute_stack[-2]) == 0:
                                attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(
                                    attribute_stack[-2].keys()[0])
                    except:
                        raise BrassException(sys.exc_info()[0], 'MDLImporter.parseXML')

                # if it doesn't contain more than one thing, it's an attribute and will need to add it to the vertex right above on the stack
                else:
                    attribute_stack[-2][attribute_stack[-2].keys()[0]] = dict(
                        attribute_stack[-2][attribute_stack[-2].keys()[0]].items() + attribute_stack[-1][
                            attribute_stack[-1].keys()[0]].items())
                    if 'uid' not in attribute_stack[-2][attribute_stack[-2].keys()[0]].keys():
                        attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(
                            attribute_stack[-2].keys()[0])
                    attribute_stack.pop()

        orientdbRestrictedIdentifier = []
        for s in set(verticesNames):
            try:
                self.orientDB_helper.create_node_class(s)
            except:
                self.orientDB_helper.create_node_class(s + '_a')

                # certain names are reserved keywords in orientdb eg: Limit, so we need to do things a little different
                orientdbRestrictedIdentifier.append(s)


        # this is the part where we add the vertices one by one to orientdb
        for e in vertices:
            # print e
            try:
                classToInsertInto = e.keys()[0]
                if classToInsertInto in orientdbRestrictedIdentifier:
                    classToInsertInto += '_a'

                if classToInsertInto == 'MDLRoot':
                    e[e.keys()[0]]['schema'] = self._mdl_schema


                self.orientDB_helper.create_node(classToInsertInto, e[e.keys()[0]])


            except:
                raise BrassException(sys.exc_info()[1], 'MDLImporter.parseXML')
                #print "insert into " + e.keys()[0] + " (" + columns + ") values (" + values + ")"



        self.orientDB_helper.create_edge_class('Containment')

        # adding containment edges
        for edge in containmentEdges:
            # print  "create edge Containment from (SELECT FROM V WHERE uid = '"+edge[0]+"') TO (SELECT FROM V WHERE uid = '"+edge[1]+"')"
            try:
                child = [condition_str('uid', edge[0])]
                parent = [condition_str('uid', edge[1])]
                self.orientDB_helper.set_containment_relationship(
                    parent_conditions=parent,
                    child_conditions=child
                )
            except:
                raise BrassException(sys.exc_info()[0], 'MDLImporter.parseXML')
                # print edge[0], edge[1]


        self.orientDB_helper.create_edge_class('Reference')

        # for some stupid reason columns are case sensitive in orientdb

        for idref in self.orientDB_helper.run_query(select_sql('V', data_to_extract=['distinct(IDREF) as idref'])):

            # sometimes we have orphans so we need to escape them.
            try:


                reference_condition = [condition_str('IDREF', idref.idref)]
                referent_condition = [condition_str('ID', idref.idref)]
                self.orientDB_helper.set_reference_relationship(
                    referent_condition=referent_condition,
                    reference_condition=reference_condition
                )
            except:
                pass

    def assignUniqueId(self, entityType):
        """
        Creates a unique id based on the entityType.

        :param str entityType:        name of the entity (ie TestMissions, RadioLinks, MDLRoot, etc)
        :return:                      a unique id in string
        """
        uniqId = ''
        if entityType in self.uniqueIdentifiers.keys():
            self.uniqueIdentifiers[entityType] += 1
        else:
            self.uniqueIdentifiers[entityType] = 0
        uniqId = entityType + '-' + str(self.uniqueIdentifiers[entityType])
        return uniqId


    def uidAlreadyAssigned(self, element):
        """
        Checks if the element already has a unique id.
        :param element:         element to check
        :return:                True or False

        """
        if 'uid' in element[element.keys()[0]].keys():
            return 1
        return 0


def main(database, config, mdlfile, remotePlocal=None):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runExample() on the processor object.
    Closes the orientDB database.

    :param str database:          orientDB database name
    :param str remotePlocal:      remote or local database, not used currently
    :return:
    """

    import os

    if not os.path.exists(config):
        BASE_DIR = os.path.dirname(os.path.realpath(__file__))
        config_file = "{0}\..\..\..\{1}".format(BASE_DIR, config)
        if not os.path.exists(config_file):
            print 'Config file does NOT exist.'
            return
    else:
        config_file = config

    try:
        processor=MDLImporter(database, mdlfile, config_file)
        processor.import_mdl()
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

    parser.add_option("-x", "--mdl",
                      help="Name and path to mdl xml file",
                      default=False)

    parser.add_option("-m", "--mode",
                      help="Mode to use in connecting to the database {plocal, remote}",
                      default=False)

    (options, args) = parser.parse_args()

    main(options.database, options.config, options.mdl, options.mode)
