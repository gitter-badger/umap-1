# USBClass.py
#
# Contains class definition for USBClass, intended as a base class (in the OO
# sense) for implementing device classes (in the USB sense), eg, HID devices,
# mass storage devices.


class USBClass:
    name = "generic USB device class"

    # maps bRequest to handler function
    request_handlers = {}

    def __init__(self, app, verbose=0):
        self.app = app
        self.interface = None
        self.verbose = verbose
        self.setup_request_handlers()

    def set_interface(self, interface):
        self.interface = interface

    def setup_request_handlers(self):
        """To be overridden for subclasses to modify self.class_request_handlers"""
        pass

    def get_mutation(self, stage, data=None):
        '''
        :param stage: stage name
        :param data: dictionary (string: bytearray) of data for the fuzzer (default: None)
        :return: mutation for current stage, None if not current fuzzing stage
        '''
        return self.app.get_mutation(stage, data)

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
