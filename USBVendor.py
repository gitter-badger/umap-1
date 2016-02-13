# USBVendor.py
#
# Contains class definition for USBVendor, intended as a base class (in the OO
# sense) for implementing device vendors.


class USBVendor:
    name = "generic USB device vendor"

    # maps bRequest to handler function
    request_handlers = {}

    def __init__(self, app, verbose=0):
        self.device = None
        self.verbose = verbose
        self.app = app

        self.setup_request_handlers()

    def set_device(self, device):
        self.device = device

    def setup_request_handlers(self):
        """To be overridden for subclasses to modify self.request_handlers"""
        pass

    def get_mutation(self, stage, data=None):
        '''
        :param stage: stage name
        :param data: dictionary (string: bytearray) of data for the fuzzer (default: None)
        :return: mutation for current stage, None if not current fuzzing stage
        '''
        return self.app.get_mutation(stage, data)
