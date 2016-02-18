# USBVendor.py
#
# Contains class definition for USBVendor, intended as a base class (in the OO
# sense) for implementing device vendors.
from USBBase import USBBaseActor


class USBVendor(USBBaseActor):
    name = "generic USB device vendor"

    # maps bRequest to handler function
    request_handlers = {}

    def __init__(self, app, verbose=0):
        super().__init__(app, verbose)
        self.device = None
        self.setup_request_handlers()

    def set_device(self, device):
        self.device = device

    def setup_request_handlers(self):
        """To be overridden for subclasses to modify self.request_handlers"""
        pass
