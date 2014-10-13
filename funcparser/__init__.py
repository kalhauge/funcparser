"""
Funcparser
==========

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

    parse_function(setup, parser)

    if functions:
        commands = parser.add_subparsers(help='Commands:')
        for func in functions:
            subparser = commands.add_parser(
                clean_name(func.__name__), help=func.__doc__
            ) 
            subparser.set_defaults(cmd=func)
            parse_function(func, subparser)

    args = vars(parser.parse_args(args))

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

def parse_function(func, parser):

    specs = getfullargspec(func)
    no_position_args = len(specs.args) - (
        len(specs.defaults) if specs.defaults else 0
    )
    for i, name in enumerate(specs.args):
        annotation = specs.annotations[name]
        clean = clean_name(name)

        if not i < no_position_args: 
            argname = '--' + clean
            default = specs.defaults[i - no_position_args]
        else:
            argname = clean
            default = None
        
        if annotation == bool:
            action = 'store_true' if not default else 'store_false'
            parser.add_argument(
                argname, action=action,
                default = default,
            )
        elif isinstance(annotation, dict):
            parser.add_argument(
                argname, 
                action=lookup(annotation),
                choices=annotation,
                default = default
            )
        elif isinstance(annotation, Counter):
            parser.add_argument(
                argname, '-' + annotation.char, 
                action='count'
            )
        else:
            parser.add_argument(
                argname, type=annotation,
                default = default
            )

all_underscores = re.compile('_')
def clean_name(name):
    return all_underscores.sub('-', name)

class Counter:
    
    def __init__(self, char):
        self.char = char

def lookup(dictionary):
    class Lookup(Action):
        def __init__(self, option_strings, dest, nargs=None, **kwargs):
            if nargs is not None:
                raise ValueError("nargs not allowed")
            super(Lookup, self).__init__(option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, dictionary[values])
    
    return Lookup

