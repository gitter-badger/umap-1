'''
Common functionality for all USB actors (interface, class, etc.)
'''


class USBBaseActor(object):

    def __init__(self, app, verbose):
        self.app = app
        self.verbose = verbose
        self.session_data = {}

    def get_mutation(self, stage, data=None):
        '''
        :param stage: stage name
        :param data: dictionary (string: bytearray) of data for the fuzzer (default: None)
        :return: mutation for current stage, None if not current fuzzing stage
        '''
        return self.app.get_mutation(stage, data)

    def get_session_data(self, stage):
        '''
        If an entity wants to pass specific data to the fuzzer when getting a mutation,
        it could return a session data here.
        This session data should be a dictionary of string:bytearray.
        The keys of the dictionary should match the keys in the templates.

        :param stage: stage that the session data is for
        :return: dictionary of session data
        '''
        return self.session_data

    def supported(self):
        '''
        Mark current USB class as supported by the host.
        This will tell the application to stop emulating current device.
        '''
        if self.app.mode == 1:
            print (' **SUPPORTED**')
            if self.app.fplog:
                self.app.fplog.write(" **SUPPORTED**\n")
            self.app.stop = True
