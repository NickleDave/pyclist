from pyclist import pyclist
from booby import Model, fields
try:
    import simplejson as json
except ImportError:
    import json  # py2.6 only

from model_helpers import query_for_model


def create_model(int_field=None, str_field=None, col_int_field=None, col_str_field=None):
    m = ExampleModelJson()
    m.int_field = int_field
    m.str_field = str_field
    m.col_int_field = col_int_field
    m.col_str_field = col_str_field
    return m


class ExampleModelJson(Model):

    int_field = fields.Integer()
    str_field = fields.String()
    col_int_field = fields.Collection(fields.Integer)
    col_str_field = fields.Collection(fields.String)

    def __str__(self):
        return "int: {0}, str: {1}, col_int: {2}, col_str: {3}".format(
            str(self.int_field), self.str_field, str(
                self.col_int_field), str(self.col_str_field)
        )


class ExampleApiJson(object):

    def __init__(self, model=None, **kwargs):

        self.model = model

    def call_return_model_for_json(self, json_str):
        '''
        Returns the json object the object was initialed with as string.

        :param json_str: a json string representing an ExampleModelJson object
        :type json_str: str
        :return: the greeting
        :rtype: str
        '''

        m_dict = json.loads(json_str)
        m = ExampleModelJson(**m_dict)

        return m

    def call_return_model_for_input(self):
        '''
        Returns the model that was created via user input.

        :return: the model
        :rtype: ExampleModelJson
        '''

        m = query_for_model(ExampleModelJson)
        return m

    def call_return_model(self):
        '''
        Returns the model that was used to initialize this object

        :return: the model
        :rtype: ExampleModelJson
        '''

        return self.model

    def call_return_model_str(self):
        '''
        Returns the 'str' representation of the model that was used to initialzie this object.

        :return: the 'str' representation of the model
        :rtype: str
        '''

        return str(self.model)


class PyclistExampleJson(object):

    def __init__(self):

        self.cli = pyclist('pyclist_json_example',
                           'A commandline wrapper example using json data.')

        self.cli.root_parser.add_argument(
            '--output', '-o', help='Filter output format')
        self.cli.root_parser.add_argument(
            '--separator', '-s', default='\n', help='Seperator for output, useful to create a comma-separated list of ids. Default is new-line')

        self.cli.add_command(ExampleApiJson, {'return_string_input': 'custom_json_string'}, {
                             'ExampleModelJson': create_model})
        self.cli.parse_arguments()

        # add some extra static arguments
        m = ExampleModelJson(int_field=1, str_field="x", col_int_field=[
                             1, 2, 3], col_str_field=['x', 'y', 'z'])
        # s = '{"int_field": 2, "str_field": "y", col_int_field: [4,5,6], col_str_field: ["a", "b", "c"]}'
        self.cli.parameters['model'] = m

        self.cli.execute()
        self.cli.print_result()


def run():
    PyclistExampleJson()

if __name__ == '__main__':
    run()
