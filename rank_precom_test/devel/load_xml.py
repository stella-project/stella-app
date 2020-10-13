import xml.etree.ElementTree as ET

tree = ET.parse('head_queries.xml')

head_queries = [hq.find('query').text for hq in tree.findall('head_query')]

pass