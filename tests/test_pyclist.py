#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pyclist
----------------------------------

Tests for `pyclist` module.
"""
import pytest

from pyclist import pyclist
from pyclist.example import ExampleApi1, ExampleModel

test_non_positional_argument = ['--ending', '.', 'print_goodbye', '--name', 'World']
test_one_positional_argument = ['--ending', '.', 'print_hello', 'World']
test_two_positional_arguments = ['--ending', '.', 'print_hello', 'World', 'another World']
test_global_argument = ['--ending', '!!!', 'print_default']
test_no_argument = ['print_default']

class TestPyclist():

    def setup_method(self, method):
        print method.__name__
        self.pyclist = pyclist.pyclist("test pyclist", "a test pyclist instance")
        self.pyclist.root_parser.add_argument('--ending', '-e', help='string or character to append to every output ,global, applicable for all sub-commands')
        self.pyclist.add_command(ExampleApi1, {'print_hello':'name'}, {'ExampleModel': ExampleModel})
        self.pyclist.parse_arguments(args=eval(method.__name__))
        self.pyclist.execute()

    def test_non_positional_argument(self):
        assert self.pyclist.result == 'Goodbye World.'

    def test_one_positional_argument(self):
        assert len(self.pyclist.result) == 1
        assert self.pyclist.result[0] == 'Hello World.'

    def test_two_positional_arguments(self):
        assert len(self.pyclist.result) == 2
        assert self.pyclist.result[0] == 'Hello World.'
        assert self.pyclist.result[1] == 'Hello another World.'

    def test_no_argument(self):
        assert self.pyclist.result == 'Oy, Stranger'

    def test_global_argument(self):
        assert self.pyclist.result == 'Oy, Stranger!!!'

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
