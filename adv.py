#!/usr/bin/env python3.4
# encoding: utf-8
"""
Parses suplied output of the command
"show route received-protocol bgp IP detail | displat xml" and send the result
to the exabgp neighbor as a valid bgp update

TODO: 
    - write XML Incremental parser as bgp full view is a huge xml file
    - add atomic, aggregator, med, local preference attributes
"""
#from sys import argv
from sys import stdout
from time import sleep
from lxml import etree
from update import Update
from bintrees import RBTree
#from pprint import pprint as pp

#_, FILE = argv

def send_update(tree):
    '''
    sends updates into stdout so exabgp can intercept/parse and send them to BGP
    neighbor
    '''
    sleep(5)
    ##Iterate through messages
    for _, value in tree.iter_items():
        stdout.write('announce ' + str(value) + '\n')
        stdout.flush()

    ##Loop endlessly to allow ExaBGP to continue running
    while True:
        sleep(1)

def ip_to_int(prefix):
    '''
    converts ip address/prefix into integer
    '''
    prefix = prefix.split('.')
    return int(prefix[0])*(256**3)   \
           + int(prefix[1])*(256**2) \
           + int(prefix[2])*(256)    \
           + int(prefix[3])          \

def get_as_path_origin_atomic(aspath):
    '''
    extracts as path, nh, origin attributes from suplied string
    '''
    asp = aspath.split(" ")
    atomic = False
    if asp[-1] not in ['I', '?']:
        atomic = True
    if atomic:
        aggregator = " ".join(asp[-2:])
        asp = [item for item in asp[2:-3] if item != '']
        origin = 'incomplete' if asp[-2] == '?' else 'igp'
        as_path = asp[:-2]
        return (' '.join(as_path), origin, atomic, aggregator)
    else:
        origin = 'incomplete' if asp[-1] == '?' else 'igp'
        as_path = asp[2:-1]
        return (' '.join(as_path), origin)

class XMLNamespaces:
    '''
    fucking junos uses xml namespace, so find, findall, iter, etc have to
    wrap namespaces into utility class
    '''
    def __init__(self, **kwargs):
        self._namespaces = {}
        for name, uri in kwargs.items():
            self.register(name, uri)

    def register(self, name, uri):
        '''
        put uri into dict for future calls
        '''
        self._namespaces[name] = '{'+uri+'}'

    def __call__(self, path):
        return path.format_map(self._namespaces)

def main():
    '''
    main
    '''
    #input_xml = etree.parse('/home/den/small_table_xml')
    input_xml = etree.parse('/home/den/full2')
    root = input_xml.getroot()
    prep = 'http://xml.juniper.net/junos/12.3R3/junos-routing'
    ns = XMLNamespaces(prep=prep)
    tree = RBTree()
    for i in root.findall(ns('{prep}route-information/ \
                             {prep}route-table/        \
                             {prep}rt')):
        prefix = i.find(ns('{prep}rt-destination')).text
        mask = i.find(ns('{prep}rt-prefix-length')).text
        key = (ip_to_int(prefix), mask)
        next_hop = i.find(ns('{prep}rt-entry/{prep}nh/{prep}to')).text
        next_hop = 'self'
        asp = i.find(ns('{prep}rt-entry/{prep}as-path')).text.rstrip()
        asp = get_as_path_origin_atomic(asp)
        community = []
        for comm in i.findall(ns('{prep}rt-entry/     \
                                 {prep}communities/   \
                                 {prep}community')):
            community.append(comm.text)
        atomic_bool = False
        if len(asp) == 2:
            as_path = asp[0]
            origin = asp[1]
        else:
            atomic_bool = True
            as_path = asp[0]
            origin = asp[1]
            atomic = asp[2]
            aggregator = asp[3]
        if atomic_bool:
            update = Update(prefix, mask, nh=next_hop, as_path=as_path,
                            origin=origin,
                            community=' '.join(community))
        else:
            update = Update(prefix, mask, nh=next_hop, as_path=as_path,
                            origin=origin,
                            community=' '.join(community))
        tree.insert(key, update)
    send_update(tree)
    #o = xmltodict.parse(etree.tostring(input_xml, encoding='utf-8'))
    #j = json.loads(json.dumps(o))
    #tree = RBTree()
    #for route in o['rpc-reply']['route-information']['route-table'][0]['rt']:
    #    prefix = route['rt-destination']
    #    mask = route['rt-prefix-length']
    #    key = (ip_to_int(prefix), mask)
    #    next_hop = route['rt-entry']['nh']['to']
    #    if 'communities' in route['rt-entry']:
    #        community = route['rt-entry']['communities']['community']
    #        if not hasattr(community, 'lower'):
    #            community = ' '.join(community)
    #    else:
    #        community = ''
    #    asp = get_as_path_origin_atomic(route['rt-entry']['as-path'])
    #    atomic_bool = False
    #    if len(asp) == 2:
    #        as_path = asp[0]
    #        origin = asp[1]
    #    else:
    #        atomic_bool = True
    #        as_path = asp[0]
    #        origin = asp[1]
    #        atomic = asp[2]
    #        aggregator = asp[3]
    #    if atomic_bool:
    #        update = Update(prefix, mask, nh=next_hop, as_path=as_path,
    #                        origin=origin,
    #                        community=community)
    #    else:
    #        update = Update(prefix, mask, nh=next_hop, as_path=as_path,
    #                        origin=origin,
    #                        community=community)
    #    tree.insert(key, update)



if __name__ == '__main__':
    main()
