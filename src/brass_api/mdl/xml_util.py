"""
xml_util.py

Contains xml serialization functions and xml validation function.

Author: Di Yao (di.yao@vanderbilt.edu)
"""

import pyorient
import os
from brass_api.common.exception_class import *

SKIP_PROPERTY_TAGS = ['uid', 'ID', 'IDREF', 'in_Containment', 'out_Containment', 'in_Reference', 'out_Reference', 'schema']

def create_tab_string(numberTabs):
    '''
    Print formatting function that creates a string consisting of
    tabs set by "numberTabs".

    :param numberTabs:  Number of tabs
    :return:            string
    '''
    s = ''
    i = 1
    while i <= numberTabs:
        s += '\t'
        i += 1
    return s


def orient_record_to_xml(record, numberTabs):
    """
    Serializes OrientRecord to xml for a vertex and writes to the xml file.
    Serialization involves traversing through a vertex's properties.
    Opening xml tag is written in this function because "ID" and "IDREF"
    properties need to be written out as xml attributes and not as xml tag text.


    :param:
                record (OrientRecord):  an orientDB record containing data about a vertex
                numberTabs (int):       number of tabs to indent before xml text
    :return:                            string

    """
    xml_str_list = []

    if record._class == 'MDLRoot':
        if 'schema' in record.oRecordData:
            xml_str_list.append( add_mdl_root_tag_attr(record.oRecordData['schema']) )
        else:
            xml_str_list.append('<MDLRoot>')
        xml_str_list.append('\n')
    else:
        xml_str_list.append( "{0}<{1}".format(create_tab_string(numberTabs), record._class) )

        if 'ID' in record.oRecordData.keys():
            xml_str_list.append(' {0}="{1}"'.format('ID', record.oRecordData['ID']) )
        elif 'IDREF' in record.oRecordData.keys():
            xml_str_list.append(' {0}="{1}"'.format('IDREF', record.oRecordData['IDREF']) )

        xml_str_list.append( ">\n" )


    for key in record.oRecordData.keys():
        if key not in SKIP_PROPERTY_TAGS:
            xml_str_list.append( '{0}<{1}>{2}</{1}>\n'.format(create_tab_string(numberTabs+1), key, record.oRecordData[key] ) )

    return ''.join(xml_str_list)


'''
The root tag in a MDL XML file has some attributes that causes exceptions for lxml parser.
Therefore these attributes need to be removed by importer and added back in by the exporter. 
'''
def add_mdl_root_tag_attr(mdl_schema):
    """
    Creates a string for <MDLRoot> that includes tmats xsd files mdl schema xsd files.
    These attributes are removed during importing because they caused xml parsing to fail.

    :param mdl_schema:      name of the mdl schema file
    :return:
    """
    mdl_root_str = '<MDLRoot xmlns="http://www.wsmr.army.mil/RCC/schemas/MDL"\
    xmlns:tmatsCommon="http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsCommonTypes"\
    xmlns:tmatsP="http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsPGroup"\
    xmlns:tmatsD="http://www.wsmr.army.mil/RCC/schemas/TMATS/TmatsDGroup"\
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
    xsi:schemaLocation="http://www.wsmr.army.mil/RCC/schemas/MDL {0}">'.format(mdl_schema)
    return mdl_root_str

def remove_mdl_root_tag_attr(xmlfile):
    """
    Removes the xml attributes of the <MDLRoot> in the xmlfile
    as all the inclusions of tmats xsd files causes parsing to fail.
    The modified xml is saved inline.

    :param xmlfile:     name and path of xml file
    :return:
    """
    import fileinput, re

    mdl_schema = None
    mdl_root_str = None

    for lines in fileinput.FileInput(xmlfile, inplace=1):
        if lines.startswith('<MDLRoot'):
            print '<MDLRoot>'
            mdl_root_str = lines
        else:
            print lines,

    matchObj = re.search('MDL_(.*)xsd', mdl_root_str)
    if matchObj is not None:
        mdl_schema = matchObj.group(0)

    return mdl_schema


def validate_mdl(xmlfile_path, mdl_schema):
    """

    :param xmlfile_path:        name and path of xml file to validate
    :param mdl_schema:          name of mdl_schema
    :return:
    """
    from lxml import etree

    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    mdl_schema = "{0}/../include/mdl_xsd/{1}".format(BASE_DIR, mdl_schema)


    try:
        schema_doc = etree.parse(mdl_schema)
        schema = etree.XMLSchema(schema_doc)

        with open(xmlfile_path) as f:
            doc = etree.parse(f)

        schema.assertValid(doc)

    except etree.XMLSchemaParseError as e:
        raise BrassException('Invalid MDL Schema File: ' + e.message, 'xml_util.validate_mdl')
    except etree.DocumentInvalid as e:
        raise BrassException('Invalide MDL XML File: ' + e.message, 'xml_util.validate_mdl')

