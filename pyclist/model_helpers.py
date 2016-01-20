import booby
from booby import fields
from booby.inspection import get_fields, is_model
from booby.validators import Required
from pydoc import locate
from collections import OrderedDict
from menus import BaseMenu, Engine
from collections import OrderedDict

import readline

MODEL_MAP = {}


class tabCompleter(object):
    """
    A tab completer that can either complete from
    the filesystem or from a list.

    Partially taken from:
    http://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
    """

    def createListCompleter(self, ll):
        """
        This is a closure that creates a method that autocompletes from
        the given list.

        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """

        def listCompleter(text, state):
            line = readline.get_line_buffer()

            if not line:
                return [c + " " for c in ll][state]

            else:
                return [c + " " for c in ll if c.startswith(line)][state]

        self.listCompleter = listCompleter


def get_type(model):

    if type(model) == fields.Integer or model == fields.Integer:
        return 'Integer'
    elif type(model) == fields.String or model == fields.String:
        return 'String'
    else:
        return model.__name__


def is_required(field):

    return next((True for x in field.validators if isinstance(x, Required)), False)


def convert_to_proper_base_type(base_type, value):
    '''
    Converts the string input in the appropriate value type.
    '''

    if get_type(base_type) == 'Integer':
        return int(value)
    elif get_type(base_type) == 'String':
        return value
    elif get_type(base_type) == 'Boolean':
        return bool(value)
    else:
        return value


def ask_details_for_type(model_type, ask_only_required=True, help_map={}):
    '''
    Asks for user input to create an object of a specified type.

    If the type is registered in a model/builder map, the function associated
    with this type is used to create the object instead of the auto-generated
    query.
    '''

    if MODEL_MAP.get(model_type, None):

        func = MODEL_MAP[model_type]
        return func()

    required_details = OrderedDict()
    non_required_details = OrderedDict()

    values = {}

    for k, f in sorted(get_fields(model_type).iteritems()):
        if is_required(f):
            required_details[k] = f
        else:
            non_required_details[k] = f

    print
    print "Enter values for fields below. Enter '?' or '? arg1 [arg2]' for help for each field."
    print
    print "Required fields:"
    print "----------------"
    print
    for k, f in required_details.iteritems():
        while True:
            value = ask_detail_for_field(k, f, ask_only_required, help_map)
            if value:
                values[k] = value
                break
            else:
                print
                print "This is a required field, please enter value for {}.".format(k)

            print

    if not ask_only_required:

        print
        print "Optional fields, press 'Enter' to ignore a field."
        print "-------------------------------------------------"
        print

        for k, f in non_required_details.iteritems():
            value = ask_detail_for_field(k, f, ask_only_required, help_map)

            if value:
                values[k] = value

            print

    obj = model_type(**values)

    return obj


def ask_collection_detail(name, detail_type, ask_only_required=True, help_map={}):

    result = []
    print "Enter details for '{}', multiple entries possible, press enter to continue to next field.".format(name)
    print
    while True:
        cd = ask_detail_for_field(
            name, detail_type, ask_only_required, help_map)
        if not cd:
            break
        else:
            result.append(cd)

    return result


def parse_for_help(answer, help_func):

    if answer.startswith('?'):
        args = answer.split(' ')[1:]
        if not help_func:
            print 'Sorry, no help available for this field.'
        else:
            print
            help_func(*args)
            print
        return True
    else:
        return False


def ask_simple_field(name, field_type, help_map={}):

    type_name = get_type(field_type)
    answer = raw_input(" - {} ({}): ".format(name, type_name))
    if not answer:
        return None

    if parse_for_help(answer, help_map.get(name, None)):
        return ask_simple_field(name, field_type, help_map)

    try:
        value = convert_to_proper_base_type(field_type, answer)
    except Exception as e:
        print "Can't convert input: ", e
        return ask_simple_field(name, field_type, help_map)

    return value


def ask_detail_for_field(name, detail_type, ask_only_required=True, help_map={}):

    value = None

    if MODEL_MAP.get(type(detail_type), None):
        func = MODEL_MAP[type(detail_type)]
        value = func()
        return value

    # collections are a special case
    if type(detail_type) == booby.fields.Collection:
        # collection
        value = ask_collection_detail(
            name, detail_type.model, ask_only_required, help_map)

    elif is_model(detail_type):
        # collection, and model field
        value = ask_details_for_type(detail_type, ask_only_required, help_map)

    elif issubclass(type(detail_type), booby.fields.Field):
        # non-collection, and non-model field
        value = ask_simple_field(name, type(detail_type), help_map)

    elif issubclass(detail_type, booby.fields.Field):
        # collection, and non-model field
        value = ask_simple_field(name, detail_type, help_map)

    return value
