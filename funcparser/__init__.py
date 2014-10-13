"""
Copyright (C) 2014 Christian Gram Kalhauge

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>.

Funcparser
==========

.. currentmodule:: funcparser
.. moduleauthor:: Christian Gram Kalhauge <christian@kalhauge.dk>

An parser equivalent to the argparser, making it easy for the user to move
their libraries form functions to CLI. It uses the python function annotations
and does therefor require a minimum python of 3.X.

.. autofunction:: parse_args

"""

__VERSION__ = '0.1'

from argparse import ArgumentParser, Action
from inspect import getfullargspec

import sys
import re

def parse_args(setup, functions=[], args=None):
    """
    :param setup: The setup function, this function should take all the general
        arguments which setup a logger, global variables, ect. The docstring
        of this method will be used as the help of the command line
        interface.

    :param functions: These functions are the commands of the program,
        annotated with type, or better the custom funcparser arguments.
    """
    if args is None: args = sys.args[1:]
    parser = ArgumentParser(description=setup.__doc__) 

    parse_function(parser, setup)

    if functions:
        commands = parser.add_subparsers(help='Commands:')
        for func in functions:
            subparser = commands.add_parser(
                clean_name(func.__name__), help=func.__doc__
            ) 
            subparser.set_defaults(cmd=func)
            parse_function(subparser, func)

    args = vars(parser.parse_args(args))

    print(args)

    general = {}
    setup_specs = getfullargspec(setup)
    for name in setup_specs.args:
        if name in args: general[name] = args.pop(name)

    result = setup(**general)

    if functions and 'cmd' in args:
        cmd = args.pop('cmd')
        result = cmd(**args)

    if result:
        print(result)

def parse_function(parser, func):
    specs = getfullargspec(func)
    no_position_args = len(specs.args) - (
        len(specs.defaults) if specs.defaults else 0
    )
    for i, name in enumerate(specs.args):
        annotation = specs.annotations[name]
        clean = clean_name(name)
        if not i < no_position_args: 
            default = specs.defaults[i - no_position_args]
        else:
            default = None
        
        parse_argument(parser, name, specs.annotations[name], default)
        

def parse_argument(parser, name, annotation, default=None, dest=None):
    argname = clean_name(name)
    if not default is None or dest: 
        argname = '--' + argname

    action = 'store' 
    choices = None
    type_ = str

    if annotation == bool:
        action = 'store_true' if not default else 'store_false'
    elif isinstance(annotation, dict):
        action = lookup(annotation)
        choices = annotation
    elif isinstance(annotation, Counter):
        action = 'count'
        dest = dest if dest else name
        argname = '-' + annotation.char
    else:
        type_ = annotation

    if isinstance(annotation, OneOf):
        if not default is None:
            parser.set_defaults(**{name: default})
        meg = parser.add_mutually_exclusive_group(required=default is None)
        for key, subtype in annotation.options.items():
            parse_argument(meg, key, subtype, dest=name)
    else: 
        kwargs=dict(
            dest=dest,
            type=type_,
            action=action, 
            choices=choices,
            default=default
        )
        if not dest: del kwargs['dest']
        if action in {'count', 'store_true'}: 
            del kwargs['type']
            del kwargs['choices']
        parser.add_argument(argname, **kwargs)


all_underscores = re.compile('_')
def clean_name(name):
    return all_underscores.sub('-', name)

class Counter:
    
    def __init__(self, char):
        self.char = char

class OneOf:
    
    def __init__(self, **kwargs):
        self.options = kwargs

def lookup(dictionary):
    class Lookup(Action):
        def __init__(self, option_strings, dest, nargs=None, **kwargs):
            if nargs is not None:
                raise ValueError("nargs not allowed")
            super(Lookup, self).__init__(option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, dictionary[values])
    
    return Lookup

