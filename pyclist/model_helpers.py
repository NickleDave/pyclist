import booby
from booby import fields
from booby.inspection import get_fields, is_model
from booby.validators import Required
from pydoc import locate
from collections import OrderedDict
from collections import OrderedDict
from tabulate import tabulate

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


def ensure_json_value(value):

    if is_model(value):
        return dict(value)
    else:
        return value


def ensure_json(value):

    if isinstance(value, (list, tuple)):
        return [ensure_json_value(w) for w in value]
    else:
        return ensure_json_value(value)


class EditModel(object):

    def __init__(self, model_type, current_value, help_map):
        self.model_type = model_type
        self.current_value = current_value
        self.new_value = {}
        self.help_map = help_map

    def get_fields(self):
        required_details = OrderedDict()
        non_required_details = OrderedDict()

        for k, f in sorted(get_fields(self.model_type).iteritems()):
            if is_required(f):
                required_details[k] = f
            else:
                non_required_details[k] = f

        details = OrderedDict()
        for k, f in required_details.iteritems():
            details[k] = f
        for k, f in non_required_details.iteritems():
            details[k] = f

        return details

    def edit_field(self, field_name):

        new_field_value = self.ask_field(field_name)
        # field = get_fields(self.current_value).get(field_name)
        value = ensure_json(new_field_value)
        self.new_value[field_name] = value

    def ask_field(self, field_name):
        field_type = self.model_type.__dict__.get(field_name, None)

        if not field_type:
            print "No field of that name."

        new_value = ask_detail_for_field(
            field_name, field_type, None, self.help_map)

        if is_model(new_value):
            new_value = new_value.to_json()

        return new_value

    def print_current(self):
        fields = self.get_fields()

        table = []
        i = 1
        for k, v in fields.iteritems():
            value = getattr(self.current_value, k, None)
            row = [k, convert_for_print(value)]
            table.append(row)
            i = i + 1

        print tabulate(table)

    def print_new(self):
        print self.new_value


def convert_value_to_print(value):

    f = getattr(value, 'to_json', None)
    if callable(f):
        value = value.to_json()

    return value


def convert_for_print(value):

    if isinstance(value, (list, tuple)):
        if len(value) > 0:
            value = (convert_value_to_print(w) for w in value)
            value = "[" + ", ".join(value) + "]"
        else:
            value = ""
    else:
        value = convert_value_to_print(value)

    return value


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


def edit_details_for_type(model_type, old_object, help_map={}):
    '''
    Asks for user input to change an existing model.
    '''

    m = EditModel(model_type, old_object, help_map)

    print
    print "Current values:"
    print
    m.print_current()
    print
    selection = "xxx"

    print
    print "Caution: the new value will replace the old value, not be added to it."
    print

    while selection:
        selection = raw_input("field to edit ('enter' to finish): ")
        if selection:
            print
            m.edit_field(selection)
            print

    return m.new_value


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
