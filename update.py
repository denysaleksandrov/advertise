#!/usr/bin/env python3.4
# encoding: utf-8

from functools import partial
from inspect import Signature, Parameter

def make_sig(*names):
    parms = [Parameter('prefix', Parameter.POSITIONAL_ONLY, default = None),
             Parameter('mask', Parameter.POSITIONAL_ONLY, default = None),
             Parameter('nh', Parameter.POSITIONAL_OR_KEYWORD, default = None),
             Parameter('as_path', Parameter.POSITIONAL_OR_KEYWORD, 
                       default = ''),
             Parameter('community', Parameter.POSITIONAL_OR_KEYWORD,
                       default = ''),
             Parameter('origin', Parameter.POSITIONAL_OR_KEYWORD,
                       default = 'incomplete')]
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

    _fields = ['prefix', 'mask', 'nh', 
               'as_path', 'community', 'origin']

    __slotes__ = [ '_' + item for item in _fields ]

    for item in _fields:
        vars()[item] = custom_property(item)
    #vars()['red'] = custom_property('red')

    def __repr__(self):
        s = 'Update('
        for id, item in enumerate(self._fields):
            if id <= 3: 
                s += '{0}, '.format(self.__dict__['_' + item])
            elif id > 3 and id != len(self._fields) - 1:
                s += "{0}='{1}', ".format(item, self.__dict__['_' + item])
            else:
                s += "{0}='{1}')".format(item, self.__dict__['_' + item])
        return s

    def __str__(self):
        s = 'route ' + self._prefix + '/' + self._mask \
            + ' next-hop ' + self._nh                  \
            + ' origin ' + self._origin                \
            + ' as-path [' + self._as_path + ']'       \
            + ' community [' + self._community + ']'
        return s

if __name__ == '__main__':
    
    n1 = Update('1.0.128.0', '24', nh='193.110.48.229', as_path='65201',
              origin='incomplete')
    print(n1.nh)
    print(n1.as_path)
    print(n1.community)
    n2 = Update('1.0.0.0', '24', nh='193.110.48.229', as_path='56203', 
                origin='incomplete', community='702:1020')
    print(n2)
