#!/usr/bin/env python3.4
# encoding: utf-8
"""
Parses suplied output of the command
"show route received-protocol bgp IP detail | displat xml" and send the result
to the exabgp neighbor as a valid bgp update

TODO: 
    - add lables and mpbgp
"""
import re
import ipaddress
from sys import stdout
from time import sleep
from lxml import etree
from update import Update
from bintrees import RBTree
from xml.etree.ElementTree import iterparse

def send_update(tree):
    '''
    sends updates into stdout so exabgp can intercept/parse and send them to BGP
    neighbor
    '''
    #sleep(5)
    ##Iterate through messages
    #for _, value in tree.iter_items():
    #    stdout.write('announce ' + str(value) + '\n')
    #    stdout.flush()
    #I tried to send vpnv4 update, it doesn't work
    #also exabgp has starnge behaviour when it converts extended-comminity from
    #from string to a send value, so it's better to use hex from as below
    stdout.write('announce route 1.4.0.0/16 rd 65000:1 next-hop self community 100:1 extended-community 0x0002FDE900000001 label 1000\n')
    stdout.flush()
    stdout.write('announce route 60.60.60.60/16 rd 1.1.1.1:5000 next-hop '
                 + '172.30.152.20 extended-community 0x0102010101011388 '
                 + 'label 301301\n')
    stdout.flush()
    ##Loop endlessly to allow ExaBGP to continue running
    while True:
        sleep(1)

def ip_to_int(prefix):
    '''
    converts ip address/prefix into integer
    '''
    #prefix = prefix.split('.')
    #return int(prefix[0])*(256**3)   \
    #       + int(prefix[1])*(256**2) \
    #       + int(prefix[2])*(256)    \
    #       + int(prefix[3])          \
    return int(ipaddress.ip_address(prefix))

def get_as_path_origin_atomic(aspath):
    '''
    extracts as path, nh, origin attributes from suplied string
    '''
    asp = aspath.split(" ")
    atomic = False
    if asp[-1] not in ['I', '?']:
        atomic = True
    if atomic:
        aggregator = ":".join(asp[-2:])
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
    junos uses xml namespace, so find, findall, iter, etc have to
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

def parse_and_remove(file, path):
    '''
    allows incremental processing of XML documents
    '''
    path_parts = path.split('/')
    context = iterparse(file, ('start', 'end'))
    next(context)
    tag_stack = []
    elem_stack = []
    for event, elem in context:
        if event == 'start':
            tag = re.sub('{[^}]*}', '', elem.tag)
            tag_stack.append(tag)
            elem_stack.append(elem)
        elif event == 'end':
            if tag_stack == path_parts:
                yield elem
                elem_stack[-2].remove(elem)
            try:
                tag_stack.pop()
                elem_stack.pop()
            except IndexError:
                pass

def create_tree(file, tree, prep, ns):
    for i in file:
        prefix = i.find(ns('{prep}rt-destination')).text
        mask = i.find(ns('{prep}rt-prefix-length')).text
        key = (ip_to_int(prefix), mask)
        kwargs = {}
        kwargs['nh'] = i.find(ns('{prep}rt-entry/{prep}nh/{prep}to')).text
        kwargs['nh'] = 'self'
        if key[0] > 4294967295:
            kwargs['nh'] = '::ffff:172.30.152.20'
        asp = i.find(ns('{prep}rt-entry/{prep}as-path')).text.rstrip()
        asp = get_as_path_origin_atomic(asp)
        community = ''
        for comm in i.findall(ns('{prep}rt-entry/{prep}communities/{prep}community')):
            community += comm.text + ' '
        kwargs['community'] = community
        if len(asp) == 2:
            kwargs['as_path'] = asp[0]
            kwargs['origin'] = asp[1]
        else:
            kwargs['as_path'] = asp[0]
            kwargs['origin'] = asp[1]
            kwargs['aggregator'] = asp[3]
        med = i.find(ns('{prep}rt-entry/{prep}med'))
        lp =  i.find(ns('{prep}rt-entry/{prep}local-preference'))
        if med is not None:
            kwargs['med'] = med.text
        if lp is not None:
            kwargs['lp'] = lp.text

        update = Update(prefix, mask, **kwargs)
        tree.insert(key, update)

def main():
    '''
    main
    '''
    files = []
    try:
        input_xml = parse_and_remove('/home/den/small_table_xml',
                                     'route-information/route-table/rt')
        files.append(input_xml)
    except FileNotFoundError:
        pass
    try:
        ipv6_input_xml = parse_and_remove('/home/den/ipv6_xml',
                                          'route-information/route-table/rt')
        files.append(ipv6_input_xml)
    except FileNotFoundError:
        pass

    tree = RBTree()
    prep = 'http://xml.juniper.net/junos/12.3R3/junos-routing'
    ns = XMLNamespaces(prep=prep)

    for file in files:
        create_tree(file, tree, prep, ns)
    send_update(tree)


if __name__ == '__main__':
    main()
