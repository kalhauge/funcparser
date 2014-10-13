
from funcparser import parse_args, Counter, clean_name, OneOf
from argparse import FileType

import sys
import io

def test_setup():
    verbose_ = None
    logfile_ = None
    
    def setup(verbose: Counter('v')=0, logfile: FileType('w')=sys.stdout):
        """ This is a function """
        nonlocal verbose_, logfile_
        print('Hello', verbose, logfile)
        verbose_ = verbose
        logfile_ = logfile

    parse_args(setup, [], '-vv --logfile /tmp/log.txt'.split())
    
    assert verbose_ == 2
    assert isinstance(logfile_, io.TextIOBase)



def test_clean_name():
   
    assert clean_name('some_name') == 'some-name'
    assert clean_name('a_long_name_with_underscores') == (
        'a-long-name-with-underscores'
    )


def test_functions():
   
    result = None
    def setup():
        nonlocal result
        result = 'setup' 

    def special_function(name: str, other_name: str = 'hello'):
        nonlocal result
        result = name, other_name


    parse_args(setup, [special_function], 
        'special-function first --other-name second'.split()
    )
    assert result == ('first', 'second')


    parse_args(setup, [special_function], 
        'special-function athing'.split()
    )
    assert result == ('athing', 'hello')
    
    parse_args(setup, [special_function], 
        ''.split()
    )
    assert result == 'setup' 


def test_dict():

    numbers = {
        'one' : 1, 
        'two' : 2,
        'three' : 3,
    }
   
    result = None
    def setup(number: numbers):
        nonlocal result
        result = number 

    parse_args(setup, [], 'one'.split())
    assert result == 1

    parse_args(setup, [], 'two'.split())
    assert result == 2

    parse_args(setup, [], 'three'.split())
    assert result == 3
   
    try:
        parse_args(setup, [], 'four'.split())
    except SystemExit: pass
    else: assert False


def test_advanced_option():

    result = None
    def setup(
            some_value: OneOf(
                integer=int, 
                counter=Counter('a'), 
                binary=lambda x: int(x, 2)
            )
    ):
        nonlocal result
        result = some_value
        
    
    parse_args(setup, [], '--integer 1'.split())
    assert result == 1

    parse_args(setup, [], '--binary 11111111'.split())
    assert result == 255
    
    parse_args(setup, [], '-aaaa'.split())
    assert result == 4





