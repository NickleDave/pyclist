from pyclist import pyclist

class ExampleModel(object):

    def __init__(self, string):

        self.name = string


class ExampleApi1(object):

    def __init__(self, ending, **kwargs):

        if ending:
            self.ending = ending
        else:
            self.ending = ''


    def call_print_hello(self, name):
        '''
        Prints hello.

        :param name: the name to print
        :type name: ExampleModel
        :return: nothing
        :rtype: None
        '''

        print "Hello {0}{1}".format(name.name, self.ending)

    def call_print_goodbye(self, name):
        '''Prints goodbye.

        That's it, just prints goodbye. With the name specified. And, if applicable, the ending.

        :param name: the name to print
        :type name: str
        :return: nothing
        :rtype: None
        '''

        print "Goodbye {0}{1}".format(name, self.ending)


class PyclistExample(object):

    def __init__(self):

        self.cli = pyclist('pyclist_example', 'A commandline wrapper example.')

        self.cli.root_parser.add_argument('--ending', '-e', help='string or character to append to every output ,global, applicable for all sub-commands')

        self.cli.add_command(ExampleApi1, {'print_hello':'name'}, {'ExampleModel': ExampleModel})

        self.cli.parse_arguments()

        result = self.cli.execute()



def run():
    PyclistExample()
