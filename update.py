#!/usr/bin/env python3.4
# encoding: utf-8

from functools import partial
from inspect import Signature, Parameter

def make_sig(*names):
    parms = [Parameter('prefix', Parameter.POSITIONAL_ONLY, default = None),
             Parameter('mask', Parameter.POSITIONAL_ONLY, default = None),
             Parameter('nh', Parameter.POSITIONAL_OR_KEYWORD, default = None),
             Parameter('as_path', Parameter.POSITIONAL_OR_KEYWORD, 
                       default = None),
             Parameter('community', Parameter.POSITIONAL_OR_KEYWORD,
                       default = ''),
             Parameter('origin', Parameter.POSITIONAL_OR_KEYWORD,
                       default = 'incomplete'),
             Parameter('lp', Parameter.POSITIONAL_OR_KEYWORD,
                       default = ''),
             Parameter('med', Parameter.POSITIONAL_OR_KEYWORD,
                       default = ''),
             Parameter('aggregator', Parameter.POSITIONAL_OR_KEYWORD,
                       default = ''),
            ]
    return Signature(parms)

class StructureMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        clsdict['__signature__'] = make_sig(*clsdict.get('_fields', []))
        return super().__new__(cls, clsname, bases, clsdict)

class Structure(metaclass=StructureMeta):
    _fields = []
    def __init__(self, *args, **kwargs):
        if 'community' not in kwargs:
            comm = self.__signature__.parameters.get('community')
            kwargs[comm.name] = comm.default
        bound_values = self.__signature__.bind(*args, **kwargs)
        for name, value in bound_values.arguments.items():
            setattr(self, name, value)

def custom_property(name):
    storage_name = '_' + name

    @property
    def prop(self):
        #print("Get prop {}".format(storage_name))
        return getattr(self, storage_name)
    
    @prop.setter
    def prop(self, value):
        #print("Set prop {} to {}".format(storage_name, value))
        setattr(self, storage_name, value)
    return prop

class Update(Structure):

    _fields = ['prefix', 'mask', 'nh', 'as_path', 'community', 'origin', 
               'lp', 'med', 'aggregator']

    __slotes__ = [ '_' + item for item in _fields ]

    for item in _fields:
        vars()[item] = custom_property(item)
    #vars()['red'] = custom_property('red')

    def __repr__(self):
        s = 'Update('
        for id, item in enumerate(self._fields):
            if id <= 1: 
                s += '{0}, '.format(self.__dict__['_' + item])
            else:
                if '_' + item in self.__dict__.keys():
                    if self.__dict__['_' + item] not in ['', False]:
                        s += "{0}='{1}', ".format(item, self.__dict__['_' + item])
        s = s[:-2] + ')'
        return s

    def __str__(self):
        s = 'route ' + self._prefix + '/' + self._mask \
            + ' next-hop ' + self._nh                  \
            + ' origin ' + self._origin                \
            + ' as-path [' + self._as_path + ']'       
        for item in self.__dict__.keys():
            if item not in ['_prefix', '_nh', '_as_path', '_origin', '_mask']:
                if self.__dict__[item] == '':
                    continue
                if item == '_community':
                    s += ' community [' + self._community + ']'
                elif item == '_lp':
                    s += ' local-preference ' + self._lp
                elif item == '_aggregator':
                    s += ' atomic-aggregate aggregator ( {} )'.format(self._aggregator)
                else:
                    s += ' {} {}'.format(item[1:], self.__dict__[item])

        return s

if __name__ == '__main__':
    
    n1 = Update('1.0.128.0', '24', nh='193.110.48.229', as_path='65201',
              origin='incomplete', lp='10', med='100')
    n2 = Update('1.0.0.0', '24', nh='193.110.48.229', as_path='56203', 
                origin='incomplete', community='702:1020')
    n3 = Update('1.10.0.0', '24', nh='193.110.48.229', as_path='56203 3132', 
                origin='incomplete', aggregator='1.1.1.1')
    print(n2)
    print(n1)
    print(n3)
    print(repr(n1))
    print(repr(n2))
    print(repr(n3))
