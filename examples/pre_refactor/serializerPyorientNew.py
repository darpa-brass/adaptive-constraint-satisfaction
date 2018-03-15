from lxml import etree
import os
import json
import sys
import pyorient

# to run: python serializer.py myXME.xme myOrientDbDatabase plocal/remote
class Processor(object):
  def __init__(self, configFile):
    data_file= open(configFile, 'r')
    config_data = json.load(data_file)
    data_file.close()
    self.username = config_data['server']['username']
    self.password = config_data['server']['password']
    server = config_data['server']['address']
    port =  config_data['server']['port']
    self.client = pyorient.OrientDB(server, port)
    self.session_id = self.client.connect( self.username, self.password )
    self.loadrObject = []
    self.uniqueIdentifiers = {}
    self.db_username = None
    self.db_password = None
    if 'database' in config_data:
      if 'username' in config_data['database'] and 'password' in config_data['database']:
        self.db_username = config_data['database']['username']
        self.db_password = config_data['database']['password']


  def initDatabase(self, database):
    if self.client.db_exists( database):
      self.client.db_drop( database )
    self.client.db_create( database, pyorient.DB_TYPE_GRAPH)

    if self.db_password != None and self.db_username != None:
      self.client.command( "create user {0} identified by {1} role [writer,reader]".format(self.db_username, self.db_password) )

  def parseXML(self, xmlFile):
    #this is a stack we maintain when traversing the xml tree
    attribute_stack = []

    #after we decide something should be a vertex we add it to the vertex list
    vertices = []

    # a list of the vertices names (which could also be derived from vertices)
    #     so we know what OrientDB classes to create
    verticesNames = []

    #the two types of edges
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
          item[el]=elem.attrib[el]
        attribute_stack.append({elem.tag:item})

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

        #if the last attribute on the stack contains more than one thing, it's a vertex
        if len(attribute_stack[-1][attribute_stack[-1].keys()[0]].keys())>1:
          try:
            attribute_stack[-1][attribute_stack[-1].keys()[0]].pop(attribute_stack[-1].keys()[0])
          except:
            pass
                      
          a = attribute_stack.pop()
          #if it doesn't have a unique identifier, will assign and also assign uid for the parent
          if self.uidAlreadyAssigned(a)==0:
            a[a.keys()[0]]['uid'] = self.assignUniqueId(a.keys()[0])
          try:
            if self.uidAlreadyAssigned(attribute_stack[-1])==0:
              attribute_stack[-1][attribute_stack[-1].keys()[0]]['uid']=self.assignUniqueId(attribute_stack[-1].keys()[0])
          except:
            pass

          #adding to the vertices list
          vertices.append(a)
          verticesNames.append(a.keys()[0])
          try:
            
            #creating a containment edge
            containmentEdges.append([a[a.keys()[0]]['uid'], attribute_stack[-1][attribute_stack[-1].keys()[0]]['uid']])
          except:
            pass

          try:
            if len(attribute_stack) > 1:
              if self.uidAlreadyAssigned(attribute_stack[-2])==0:
                attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(attribute_stack[-2].keys()[0])
          except:
            print "Unexpected error:", sys.exc_info()[0]
        
        # if it doesn't contain more than one thing, it's an attribute and will need to add it to the vertex right above on the stack
        else:
          attribute_stack[-2][attribute_stack[-2].keys()[0]]=dict(attribute_stack[-2][attribute_stack[-2].keys()[0]].items()+attribute_stack[-1][attribute_stack[-1].keys()[0]].items())          
          if 'uid' not in attribute_stack[-2][attribute_stack[-2].keys()[0]].keys():
            attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(attribute_stack[-2].keys()[0])
          attribute_stack.pop()
   

    orientdbRestrictedIdentifier = []
    for s in set(verticesNames):
      try:
        self.client.command( "create class "+s+" extends V clusters 1" )
      except:
         self.client.command( "create class "+s+"_a extends V clusters 1" )
         
         #certain names are reserved keywords in orientdb eg: Limit, so we need to do things a little different
         orientdbRestrictedIdentifier.append(s)

      print  "create class "+s+" extends V clusters 1"
    
    
    #this is the part where we add the vertices one by one to orientdb 
    for e in vertices:
      #print e
      try:
        columns = ''
        values = '' 
        for el in e[e.keys()[0]].keys():
          if columns != '':
            columns += ' ,'
          if values != '':
            values += ' ,'
          columns += el
          values +=  "'"+e[e.keys()[0]][el]+"'"

        classToInsertInto = e.keys()[0]
        if classToInsertInto in orientdbRestrictedIdentifier:
          classToInsertInto += '_a'

        self.client.command( "insert into "+ classToInsertInto +" ("+columns+") values ("+ values+")")
        print  "insert into "+ e.keys()[0]+" ("+columns+") values ("+ values+")"
        #self.client.command('commit')
        #self.client.command( "insert into "+e.keys()[0] )
      except:
        print "Unexpected error:", sys.exc_info()[0]
        print "insert into "+ e.keys()[0]+" ("+columns+") values ("+ values+")"
        
    
    self.client.command( "create class Containment extends E clusters 1" )
    #adding containment edges
    for edge in containmentEdges:
      #print  "create edge Containment from (SELECT FROM V WHERE uid = '"+edge[0]+"') TO (SELECT FROM V WHERE uid = '"+edge[1]+"')"
      try:
        self.client.command( "create edge Containment from (SELECT FROM V WHERE uid = '"+edge[0]+"') TO (SELECT FROM V WHERE uid = '"+edge[1]+"')")
      except:
        print "Unexpected error:", sys.exc_info()[0]
        #print edge[0], edge[1]

    self.client.command("create class Reference extends E clusters 1")
    #print self.client.query("select distinct(IDREF) from V")

    # for some stupid reason columns are case sensitive in orientdb
    for idref in  self.client.query("select distinct(IDREF) as idref from V"):
      print "create edge Reference from (select from V where IDREF='"+idref.idref+"') TO (select from V where ID='"+idref.idref+"')"
      
      # sometimes we have orphans so we need to escape them.
      try:
        self.client.command("create edge Reference from (select from V where IDREF='"+idref.idref+"') TO (select from V where ID='"+idref.idref+"')")
      except:
        pass
  

  def assignUniqueId(self, entityType):
    uniqId=''
    if entityType in self.uniqueIdentifiers.keys():
      self.uniqueIdentifiers[entityType]+=1
    else:
      self.uniqueIdentifiers[entityType]=0
    uniqId = entityType + '-' + str(self.uniqueIdentifiers[entityType])
    return uniqId
  
  def uidAlreadyAssigned(self, element):
    if 'uid' in  element[element.keys()[0]].keys():
      return 1
    return 0

  def closeDatabase(self):
    self.client.db_close()

  def cleanMDLRoot(self, xmlfile):
    import fileinput
    for lines in fileinput.FileInput(xmlfile, inplace=1):
      if lines.startswith('<MDLRoot'):
        print '<MDLRoot>'
      else:
        print lines,


def main(xmlFile, json_loader, database, remotePlocal):
  import shutil

  orient_mdl_file = xmlFile + '.orientdb'
  shutil.copy2(xmlFile, orient_mdl_file)

  processor=Processor('config.json')
  processor.cleanMDLRoot(orient_mdl_file)
  processor.initDatabase(database)
  processor.parseXML(orient_mdl_file)
  processor.closeDatabase()

def makeLoadrTemplate(loaderFileName, path, database):
  
  data_file= open('config.json', 'r') 
  config_data = json.load(data_file) 
  username = config_data['server']['username']
  password = config_data['server']['password']
  data_file.close()
  
if __name__ == "__main__":
  json_loader = 'loadr.json'

  if len(sys.argv) >= 4:
    xme_name = sys.argv[1]
    database = sys.argv[2]
    remotePlocal = sys.argv[3]
  else:
    print('Not enough arguments. The script should be called as following: python serializerPyorientNew.py myXME.xme myOrientDbDatabase remote')

  main(xme_name, json_loader, database, remotePlocal)
