import pyorient


SKIP_PROPERTY_TAGS = ['uid', 'ID', 'IDREF', 'in_Containment', 'out_Containment', 'in_Reference', 'out_Reference']

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


