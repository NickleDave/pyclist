# -*- coding: utf-8 -*-
import argparse
import argcomplete
import inspect
from parinx import parser
from pprint import pprint, pformat
import importlib
import logging
from restkit.errors import RequestFailed, ResourceError
import traceback
try:
    import simplejson as json
except ImportError:
    import json # py2.6 only


#TODO: make that more generic to be able to use other methods
API_MARKER = 'call'
def is_api_method(field):

    return inspect.ismethod(field) and field.__name__.startswith(API_MARKER)

def recursive_get(dict_o, key):
    '''Helper to get key from a string of the format: key1.key2.key3'''

    if not dict_o:
        return {}
    else:
        result = dict.get(dict_o, key)
        return result


def create_output_item_list(item, list_append=[]):
    '''
    Populates a list of output items.

    If the item is a list, it will be flattened and this method will be
    called recursively. If it is a string, it will be appended as is.
    If it has a method "to_json()" the result of that call will be appended.
    In all other cases json.dumps() will be called on the object and the result
    of that call will be appended.

    :param item: either a list or a single object
    :type item: list or object
    :param list_append: the list to populate
    :type list_append: list
    :return: nothing, the provided list contains a json strings
    :rtype: None
    '''

    if isinstance(item, (list, tuple)) and not isinstance(item, basestring):
        for i in item:
            create_output_item_list(i, list_append)

        return
    elif isinstance(item, basestring):
        list_append.append(item)
        return

    if hasattr(item, "to_json") and callable(getattr(item, "to_json")):
        list_append.append(item.to_json(sort_keys=True, indent=2))
    else:
        list_append.append(json.dumps(item, sort_keys=True, indent=2))


def create_type_function(arg_type, init_functions={}):
    '''
    Creates an init function for the specified type.

    This is used to be forwarded to the argparse type which in turn uses it to initiate the parameter object form a string.

    :param arg_type: the type name of the argument (using the docstring param value)
    :type arg_type: str
    :param init_functions: a dict of functions to lookup the arg_type
    :type init_functions: dict
    :return: a function to initialize the provided argument value from a string
    :rtype: method
    '''

    if init_functions.get(arg_type, None):
        i_fun = init_functions.get(arg_type)
    else:
        i_fun = eval(arg_type)

    def create(string):
        return i_fun(string)

    return create


class pyclist(object):
    '''A class to generate an argparse-based commandline parser using one
    or more api classes, and help execute the selected method using
    the right arguments.
    '''

    def __init__(self, name, description):
        '''
        Creates a pyclist instance.

        TODO: explain input maps/positional arguments

        :param name: the name of the commandline application to create
        :type name: str
        :param description: a short description of the commandline application, will be used in the generated help message.
        :type name: str
        '''

        self.argtype_translation_dict = {}  # to store the arg types of the different commands

        self.root_parser = argparse.ArgumentParser(description=description)
        self.subparsers = self.root_parser.add_subparsers(help='sub-command to run')
        self.arg_details = {}
        self.init_functions = {}


    def add_command(self, cls, positional_args={}, init_functions={}):
        '''
        Adds all methods of a class (that start with 'call_') as sub-commands.

        :param cls: the class
        :type cls: type
        :param positional_args: optional dictionary of names (ideally with only one item) of positional (instead of an optional argument) arguments, with method names as the keys
        :type positional_args: dict
        :param init_functions: optioal dictionary of functions that can initialize a certain model class using only a string, key is the name of the model class
        :type init_functions: dict
        :return: nothing
        :rtype: None
        '''

        self.init_functions[cls] = init_functions
        details = self.construct_arguments(cls, positional_args)
        self.arg_details.update(details)


    def construct_arguments(self, cls, positional_args={}):
        '''
        Adds arguments to subparsers, returns populated dict of methods and their details.

        :param cls: the class to parse for methods to use
        :type cls: type
        :param positional_args: a dict of argument names per method name which should be used as positional argument.
        :type positional_args: dict
        :rtype: dict
        :return: a dict with metadata used for creating the cli arguments with argparse
        '''

        arg_result = {}

        for method in inspect.getmembers(cls, is_api_method):

            name = method[1].__name__

            docstring = parser.get_method_docstring(cls, name)
            result = parser.parse_docstring(docstring, cls)
            result['class'] = cls
            pretty_name = name[len(API_MARKER)+1:]
            # adding argument to subparsers
            positional_arg = positional_args.get(pretty_name, None)
            result['positional_arg'] = positional_arg
            arg = self.create_arg_object(cls, pretty_name, result['arguments'], result['return'], result['description'], positional_arg)

            arg_result[pretty_name] = result


        return arg_result


    def create_arg_object(self, cls, name, arguments_dict, return_dict, description, positional_arg=None):
        '''
        Creates a commandline parser (sub-command) for an api method.

        Uses the methods 'sphinx'-doc to generate the arguments for the sub-command.

        '''
        desc = description
        return_desc = return_dict['description']

        parser = self.subparsers.add_parser(name, help=description)

        for key, value in arguments_dict.iteritems():

                arg = value['type_name']
                desc = value['description']
                required = value['required']

                arg_type = arg
                if not arg_type == 'list':
                    type_fun = create_type_function(arg_type, self.init_functions.get(cls, {}))

                    if key == positional_arg:
                        arg_name = key
                        parser.add_argument(arg_name, help=desc, type=type_fun, nargs='+')
                    else:
                        arg_name = '--'+key
                        parser.add_argument(arg_name, help=desc, required=required, type=type_fun)
                else:
                    if key == positional_arg:
                        arg_name = key
                        parser.add_argument(arg_name, help=desc, nargs='+')
                    else:
                        arg_name = '--'+key
                        parser.add_argument(arg_name, help=desc, required=required, type=str)


        parser.set_defaults(command=name)


    def parse_arguments(self, args=None):
        '''
        Parses all arguments, and stores the resulting argparse namespace in a field 'parameters' as a dict.

        Change this field before calling 'execute' if necessary.
        '''

        argcomplete.autocomplete(self.root_parser)
        self.namespace = self.root_parser.parse_args(args=args)
        self.command = self.namespace.command
        self.parameters = self.namespace.__dict__.copy()
        self.positional_arguments = False


    def execute(self):
        '''
        Calls the user-selected method with the approriate parameters.
        '''

        cls = self.arg_details[self.command]['class']
        self.api = cls(**self.parameters)

        methodToCall = getattr(self.api, API_MARKER+'_'+self.command)

        api_args = {}

        pos_arg = self.arg_details[self.command].get('positional_arg', None)

        pos_arg_values = []

        for key, value in self.arg_details[self.command]['arguments'].iteritems():

            v = vars(self.namespace)[key]

            if key == pos_arg:

                arg_type = self.arg_details[self.command]['arguments'][key]['type_name']
                if arg_type == 'list':
                    api_args[key] = v
                else:
                    pos_arg_values = v
            else:
                api_args[key] = v

        # if we have a positional argument, we execute the method for every one of those
        if pos_arg_values:
            self.result = []
            for v in pos_arg_values:
                self.positional_arguments = True
                temp_args = api_args.copy()
                temp_args[pos_arg] = v
                r = methodToCall(**temp_args)
                self.result.append(r)
        else:
            try:
                self.result = methodToCall(**api_args)
            except Exception as e:
                self.result = e

        return self.result


    def print_result(self, output_format=None, separator=u'\n', token_separator=u'\t'):
        '''
        Prints either json output, or a table of strings from the result of the method call.
        '''

        output = []
        if self.positional_arguments:
            for item in self.result:
                create_output_item_list(item, output)
        else:
            create_output_item_list(self.result, output)

        if not output_format:

            if len(output) == 1:
                print output[0]
            else:
                print "["+",\n".join(output)+"]"

        else:

            lines = []
            for o in output:
                dict_obj = json.loads(o)
                if not dict_obj:
                    continue
                line = []

                for token in output_format.split(','):
                    value = reduce(recursive_get, token.split("."), dict_obj)
                    if not value:
                        value = u''
                    line.append(unicode(value))
                lines.append(token_separator.join(line))

            print separator.join(lines).encode("utf-8")
