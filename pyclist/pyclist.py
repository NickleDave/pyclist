# -*- coding: utf-8 -*-
import argparse
import argcomplete
import inspect
from parinx import parser
from pprint import pprint, pformat

#TODO: make that more generic to be able to use other methods
API_MARKER = 'call'
def is_api_method(field):

    return inspect.ismethod(field) and field.__name__.startswith(API_MARKER)


def create_output_item(item, output_format=None):
    '''
    Helper method to pretty print results.
    '''


    result = ""

    if output_format:
        values = []
        for token in output_format.split(","):
            v = getattr(item, token)
            values.append(unicode(v).replace('\n', ' '))

        result = u'\t'.join(values).encode('utf-8')

    else:
        result = pformat(dict(item))

    return result


def create_arg_object(subparsers, name, argtype_translation_dict, arguments_dict, return_dict, description):
    '''
    Creates a commandline parser (sub-command) for an api method.

    Uses the methods 'sphinx'-doc to generate the arguments for the sub-command.
    '''
    desc = description
    return_desc = return_dict['description']

    parser = subparsers.add_parser(name, help=description)

    for key, value in arguments_dict.iteritems():

            arg = value['type_name']
            desc = value['description']
            required = value['required']

            arg_type = arg
            if arg_type not in ['str', 'int', 'bool']:
                trans_key = name+'&'+key
                argtype_translation_dict[trans_key] = arg_type
                arg_type = 'str'

            parser.add_argument('--'+key, help=desc, required=required, type=eval(arg_type))

    parser.set_defaults(command=name)


def construct_arguments(subparsers, argtype_translation_dict, cls):
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
        arg = create_arg_object(subparsers, pretty_name, argtype_translation_dict, result['arguments'], result['return'], result['description'])

        arg_result[pretty_name] = result


    return arg_result


class pycli(object):
    '''A class to generate an argparse-based commandline parser using one
    or more api classes, and help execute the selected method using
    the right arguments.
    '''

    def __init__(self, name, description):

        self.argtype_translation_dict = {}  # to store the arg types of the different commands

        self.root_parser = argparse.ArgumentParser(description=description)
        self.subparsers = self.root_parser.add_subparsers(help='sub-command to run')
        self.arg_details = {}


    def add_command(self, cls):

        details = construct_arguments(self.subparsers, self.argtype_translation_dict, cls)
        self.arg_details.update(details)


    def parse_arguments(self):

        argcomplete.autocomplete(self.root_parser)
        self.namespace = self.root_parser.parse_args()
        self.command = self.namespace.command

        cls = self.arg_details[self.command]['class']

        self.api = cls(**self.namespace.__dict__)


    def execute(self):

        methodToCall = getattr(self.api, API_MARKER+'_'+self.command)

        api_args = {}
        for key, value in self.arg_details[self.command]['arguments'].iteritems():
            v = vars(self.namespace)[key]
            trans_key = self.namespace.command + '&' + key

            if trans_key in self.argtype_translation_dict.keys():
                cls_name = self.argtype_translation_dict[trans_key]
                cls = eval(cls_name)
                v_json = json.loads(v)

                if isinstance(v_json, (list, tuple)):
                    v = cls(v_json)
                else:
                    v = cls(**v_json)

            api_args[key] = v

        self.result = methodToCall(**api_args)
        return self.result


    def print_result(self, output_format=None, separator='\n'):

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
