import sys, os
import lxml
import pyorient
from lxml import etree
from brass_print_util import *
from brass_api.brass_orientdb.brass_orientdb_helper import BrassOrientDBHelper
from brass_api.brass_orientdb.orientdb_sql import condition_str, select_sql

'''
TODO: 
[1] Add schema validation!!!!
[2] Move main() to a separate test program.
'''
class MDLImporter(object):
    def __init__(self, databaseName, mdlFile, configFile = 'config.json'):
        #self.orientDB_helper = BrassOrientDBHelper( orientdb_client=BrassOrientDBClient(databaseName, configFile) )
        self.loadrObject = []
        self.uniqueIdentifiers = {}

        self.orientDB_helper = BrassOrientDBHelper(database_name=databaseName, config_file=configFile)
        self.mdlFile = mdlFile
        self.orientDB_helper.open_database(over_write=True)

    def import_mdl(self):
        remove_mdl_root_tag_attr(self.mdlFile)
        self.parseXML(self.mdlFile)

    def parseXML(self, xmlFile):
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
                        print "Unexpected error:", sys.exc_info()[0]

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
                #DY:    self.client.command("create class " + s + " extends V clusters 1")
                self.orientDB_helper.create_node_class(s)
            except:
                #DY:    self.client.command("create class " + s + "_a extends V clusters 1")
                self.orientDB_helper.create_node_class(s + '_a')

                # certain names are reserved keywords in orientdb eg: Limit, so we need to do things a little different
                orientdbRestrictedIdentifier.append(s)

            #print  "create class " + s + " extends V clusters 1"

        # this is the part where we add the vertices one by one to orientdb
        for e in vertices:
            # print e
            try:
                classToInsertInto = e.keys()[0]
                if classToInsertInto in orientdbRestrictedIdentifier:
                    classToInsertInto += '_a'

                #DY: self.client.command("insert into " + classToInsertInto + " (" + columns + ") values (" + values + ")")
                self.orientDB_helper.create_node(classToInsertInto, e[e.keys()[0]])


            except:
                print "Unexpected error:", sys.exc_info()[1]
                #print "insert into " + e.keys()[0] + " (" + columns + ") values (" + values + ")"


        #DY: self.client.command("create class Containment extends E clusters 1")
        self.orientDB_helper.create_edge_class('Containment')

        # adding containment edges
        for edge in containmentEdges:
            # print  "create edge Containment from (SELECT FROM V WHERE uid = '"+edge[0]+"') TO (SELECT FROM V WHERE uid = '"+edge[1]+"')"
            try:
                #DY:        self.client.command("create edge Containment from (SELECT FROM V WHERE uid = '" + edge[
                #    0] + "') TO (SELECT FROM V WHERE uid = '" + edge[1] + "')")
                parent = [condition_str('uid', edge[0])]
                child = [condition_str('uid', edge[1])]
                self.orientDB_helper.set_containment_relationship(
                    parent_conditions=parent,
                    child_conditions=child
                )
            except:
                print "Unexpected error:", sys.exc_info()[0]
                # print edge[0], edge[1]

        #DY:        self.client.command("create class Reference extends E clusters 1")
        self.orientDB_helper.create_edge_class('Reference')

        # for some stupid reason columns are case sensitive in orientdb
        #DY:        for idref in self.client.query("select distinct(IDREF) as idref from V"):
        for idref in self.orientDB_helper.run_query(select_sql('V', data_to_extract=['distinct(IDREF) as idref'])):

            # sometimes we have orphans so we need to escape them.
            try:
                #DY:        self.client.command(
                #    "create edge Reference from (select from V where IDREF='" + idref.idref + "') TO (select from V where ID='" + idref.idref + "')")
                reference_condition = [condition_str('IDREF', idref.idref)]
                referent_condition = [condition_str('ID', idref.idref)]
                self.orientDB_helper.set_reference_relationship(
                    referent_condition=referent_condition,
                    reference_condition=reference_condition
                )
            except:
                pass

    def assignUniqueId(self, entityType):
        uniqId = ''
        if entityType in self.uniqueIdentifiers.keys():
            self.uniqueIdentifiers[entityType] += 1
        else:
            self.uniqueIdentifiers[entityType] = 0
        uniqId = entityType + '-' + str(self.uniqueIdentifiers[entityType])
        return uniqId


    def uidAlreadyAssigned(self, element):
        if 'uid' in element[element.keys()[0]].keys():
            return 1
        return 0

def main(database, config, mdlfile, remotePlocal=None):
    """
    Instantiates a Processor object and passes in the orientDB database name.
    Calls runExample() on the processor object.
    Closes the orientDB database.

    :argument:
                database (str):     orientDB database name
                remotePlocal (str): remote or local database, not used currently
    :return:
    """

    import os
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    config_file = "{0}/../{1}".format(BASE_DIR, config)
    if not os.path.exists(config_file):
        print 'Config file does NOT exist.'
        return

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
