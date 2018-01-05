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

  def initDatabase(self, database):
    if self.client.db_exists( database):
      self.client.db_drop( database )
    self.client.db_create( database, pyorient.DB_TYPE_GRAPH)
    #self.client.command( "create class Entity extends V" )
    #self.client.command( "create class Connection extends E" )
    #self.client.command( "create class Containment extends E" )
    #self.client.command( "create class Inheritance extends E" )
    #self.client.command( "create class Reference extends E" )

  def loadDatabase(self, database, loadrObject):
    self.loadrObject=loadrObject
    self.client.db_open(database, self.username, self.password)
    for element in self.loadrObject:
      print(repr("insert into Entity set id='"+element['id']+"', type='"+element['type']+"' , kind='"+element['kind']+"' , guid='"+element['guid']+"', edgeProperties="+ json.dumps(element['edgeProperties'])+", attributes="+ json.dumps(element['attributes'])+", `contains`='["+ ','.join(element['contains'])+"]', connects = '["+ ','.join(element['connects'])+"]', references= '["+(element['references'][0] if len(element['references']) >0 else '')+"]', name='"+ (element['name'] if element['name'] is not None else '') +"' , inherits='["+ ','.join(element['inherits'])+"]'"))
      self.client.command("insert into Entity set id='"+element['id']+"', type='"+element['type']+"' , kind='"+element['kind']+"' , guid='"+element['guid']+"', edgeProperties="+ json.dumps(element['edgeProperties'])+", attributes="+ json.dumps(element['attributes'])+", `contains`='["+ ','.join(element['contains'])+"]', connects = '["+ ','.join(element['connects'])+"]', references= '["+(element['references'][0] if len(element['references']) >0 else '')+"]', name='"+ (element['name'] if element['name'] is not None else '') +"' , inherits='["+ ','.join(element['inherits'])+"]'")
    for element in self.loadrObject:
      for edge in element['connects']:
        print("create edge Connection from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')") 
        self.client.command("create edge Connection from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"') set EdgeProp="+ json.dumps(element['edgeProperties']))
      for edge in element['contains']:
        print("create edge Containment from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')")
        self.client.command("create edge Containment from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')")
      for edge in element['inherits']:
        print("create edge Inheritance from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')")
        self.client.command("create edge Inheritance from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')")
      for edge in element['references']:
        print("create edge Reference from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')", edge, element)
        self.client.command("create edge Reference from (select from Entity where id = '"+element['id']+"') to (select from Entity where id = '"+edge+"')")
    self.client.db_close()

  def parseXML(self, xmlFile):
    attribute_stack = []
    attributes = {}
    vertices = []
    verticesNames = []
    edges = {}

    for event, elem in etree.iterparse(xmlFile, events=('start', 'end')):
      if event == 'start':
        item = {}
        item[elem.tag] = elem.text
        for el in elem.attrib.keys():
          item[el]=elem.attrib[el]
        attribute_stack.append({elem.tag:item})
      elif event == 'end':
        #print 'at: ',attribute_stack[-1], len(attribute_stack)
        if len(attribute_stack[-1][attribute_stack[-1].keys()[0]].keys())>1:
          attribute_stack[-1][attribute_stack[-1].keys()[0]].pop(attribute_stack[-1].keys()[0])
          a = attribute_stack.pop()
          vertices.append(a)
          verticesNames.append(a.keys()[0])
          #print "here: ", vertices
          try:
            #attribute_stack[-2][attribute_stack[-2].keys()[0]]['0'] = 0
            attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(attribute_stack[-2].keys()[0])
          except:
            print "Unexpected error:", sys.exc_info()[0]
        else:
          try:
            attribute_stack[-2][attribute_stack[-2].keys()[0]]=dict(attribute_stack[-2][attribute_stack[-2].keys()[0]].items()+attribute_stack[-1][attribute_stack[-1].keys()[0]].items())
            attribute_stack[-2][attribute_stack[-2].keys()[0]]['uid'] = self.assignUniqueId(attribute_stack[-2].keys()[0])
          except:
            print "Unexpected error:", sys.exc_info()[0]
          attribute_stack.pop()
    i = 0
    print 'hootay'
    print
    '''while i < len(vertices):
      try:
        #vertices[i][vertices[i].keys()[0]].pop('0')
        print vertices[i]
      except:
        pass
      i+=1'''
    print set(verticesNames)
    orientdbRestrictedIdentifier = []
    for s in set(verticesNames):
      try:
        self.client.command( "create class "+s+" extends V" )
      except:
         self.client.command( "create class "+s+"_a extends V" )
         orientdbRestrictedIdentifier.append(s)

      print  "create class "+s+" extends V"
    
    for e in vertices:
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
        self.client.command('commit')
        #self.client.command( "insert into "+e.keys()[0] )
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
    
def main(xmlFile, json_loader, database, remotePlocal):
  processor=Processor('config.json')
  processor.initDatabase(database)
  processor.parseXML(xmlFile)

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
    print('Not enough arguments. The script should be called as following: python serializer.py myXME.xme myOrientDbDatabase remote/plocal')

  main(xme_name, json_loader, database, remotePlocal)
