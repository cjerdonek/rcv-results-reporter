"""
Supports parsing Dominion XML (.xml) RCV result reports.
"""

import logging
import xml.etree.ElementTree as ET


_log = logging.getLogger(__name__)



def parse_xml_file(path):
    """
    Parse an XML file, and return a dict of results.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Parse out the contest_name.
    rcv_static_data = root.find('{RcvShortReport}RcvStaticData')
    report = rcv_static_data.find('{RcvShortReport}Report')
    tablix2 = report.find('{RcvShortReport}Tablix2')
    # TODO: will this always be "Textbox24"?
    contest_name = tablix2.attrib['Textbox24']
    metadata = {
        'contest_name': contest_name,
    }
    results = {
        '_metadata': metadata,
    }
    return results
