"""
Funcparser
==========

An parser equivalent to the argparser, making it easy for the user to move
their libraries form functions to CLI. It uses the python function annotations
and does therefor require a minimum python of 3.X.

.. autofunction:: parse_args

"""

__VERSION__ = '0.1'

from argparse import ArgumentParser
from inspect import getfullargspec

def parse_args(setup, functions):
    """
    :param setup: The setup function, this function should take all the general
        arguments which setup a logger, global variables, ect. The docstring
        of this method will be used as the help of the command line
        interface.

    :param functions: These functions are the commands of the program,
        annotated with type, or better the custom funcparser arguments.
    """
    parser = ArgumentParser(description=setup.__docs__) 

    parse_function(setup, function)

    commands = parser.add_subparsers(help='Commands:')
    for func in functions:
        subparser = commands.add_parser(func.__name__, help=func.__doc__) 
        parse_function(func, subparser)

    args = vars(parser.parse_args())

    general = {}
    setup_specs = getfullargspec(setup)
    for name in setup_specs.args:
        if name in args: general[name] = args.pop(name)

    setup(**general)

    cmd = args.pop('cmd')
    result = cmd(**args)

    if result:
        print(result)

def parse_function(function, parser):
    parser.set_defaults(func=func)

    specs = getfullargspec(func)
    no_position_args = len(specs.args) - (
        len(specs.defaults) if specs.defaults else 0
    )
    for i, name in enumerate(specs.args):
        anotation = specs.annotations[name]

        if not i < no_position_args: 
            name = '--' + name
            default = specs.defaults[i - no_position_args]
        else:
            default = None
        
        if anotation == bool:
            action = 'store_true' if not default else 'store_false'
            parser.add_argument(
                name, action=action,
                default = default
            )
        else:
            parser.add_argument(
                name, type=anotation,
                default = default
            )

        parser.add_argument(name, type=specs.annotations[name])
