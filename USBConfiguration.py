# USBConfiguration.py
#
# Contains class definition for USBConfiguration.
from struct import pack


class USBConfiguration:

    def __init__(self, app, configuration_index, configuration_string, interfaces):
        self.app = app
        self.configuration_index = configuration_index
        self.configuration_string = configuration_string
        self.configuration_string_index = 0
        self.interfaces = interfaces

        self.attributes = 0xe0
        self.max_power = 0x32

        self.device = None

        for i in self.interfaces:
            i.set_configuration(self)

    def set_device(self, device):
        self.device = device

    def set_configuration_string_index(self, i):
        self.configuration_string_index = i

    def get_descriptor(self):
        interface_descriptors = bytearray()
        for i in self.interfaces:
            interface_descriptors += i.get_descriptor()
        bLength = 9
        bDescriptorType = 2
        wTotalLength = len(interface_descriptors) + 9
        bNumInterfaces = len(self.interfaces)
        d = pack(
            '<BBHBBBBB',
            bLength,
            bDescriptorType,
            wTotalLength,
            bNumInterfaces,
            self.configuration_index,
            self.configuration_string_index,
            self.attributes,
            self.max_power
        )
        return d + interface_descriptors
