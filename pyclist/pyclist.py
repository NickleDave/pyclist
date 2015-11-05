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


def str_to_class(module_list, class_name):
    for module_name in module_list:
        try:
            module_ = importlib.import_module(module_name)
            try:
                class_ = getattr(module_, class_name)
                return class_ or None

            except AttributeError:
                logging.error('Class does not exist')
        except ImportError:
            logging.error('Module {} does not exist'.format(module_))

    raise Exception("Can't find module for {}".format(class_name))


def create_output_item(item, output_format=None):
    '''
    Helper method to pretty print results.
    '''


    result = ""

    if output_format:

        if isinstance(item, (list)):
            result = ""
            for i in item:
                values = []
                for token in output_format.split(","):
                    v = getattr(i, token)
                    values.append(unicode(v).replace('\n', ' '))

                r = u'\t'.join(values).encode('utf-8')
                if r:
                    result = result + r

        else:
        
            for token in output_format.split(","):
                v = getattr(item, token)
                values.append(unicode(v).replace('\n', ' '))

            result = u'\t'.join(values).encode('utf-8')

    else:
        if isinstance(item, (list)):
            for i in item:
                result = "{0}{1}\n".format(result, pformat(dict(i)))
        else:
            result = pformat(dict(item))

    return result


def create_type_function(arg_type, init_functions={}):

    if init_functions.get(arg_type, None):
        i_fun = init_functions.get(arg_type)
    else:
        #TODO: that probably doesn't make sense...
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


    def parse_arguments(self):
        '''
        Parses all arguments, and stores the resulting argparse namespace in a field 'parameters' as a dict.

        Change this field before calling 'execute' if necessary.
        '''

        argcomplete.autocomplete(self.root_parser)
        self.namespace = self.root_parser.parse_args()
        self.command = self.namespace.command
        self.parameters = self.namespace.__dict__.copy()



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


    def print_result(self, output_format=None, separator='\n'):

        if isinstance(self.result, Exception):
            # print "{0}: {1}".format(self.result.status_int, self.result.msg)
            # traceback.print_stack()
            print self.result
            return

        if isinstance(self.result, bool):
            print self.result
            return

        if isinstance(self.result, list):
            output = []
            for item in self.result:

                output.append(create_output_item(item, output_format))

            print separator.join(output)
            return

        else:
            output = create_output_item(self.result, output_format)
            print output
