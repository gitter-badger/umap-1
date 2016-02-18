# USBKeyboard.py
#
# Contains class definitions to implement a USB keyboard.

from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *
from .wrappers import mutable
from enum import IntEnum
from struct import pack


class Requests(IntEnum):
    GET_REPORT = 0x01  # Mandatory
    GET_IDLE = 0x02
    GET_PROTOCOL = 0x03  # Ignored - only for boot device
    SET_REPORT = 0x09
    SET_IDLE = 0x0A
    SET_PROTOCOL = 0x0B  # Ignored - only for boot device


class USBKeyboardClass(USBClass):
    name = "USB Keyboard class"

    def setup_request_handlers(self):
        self.local_handlers = {
            Requests.GET_REPORT: ('hid_get_report', self.handle_get_report),
            Requests.GET_IDLE: ('hid_get_idle', self.handle_get_idle),
            Requests.SET_REPORT: ('hid_set_report', self.handle_set_report),
            Requests.SET_IDLE: ('hid_set_idle', self.handle_set_idle),
        }
        self.request_handlers = {
            x: self.handle_all for x in self.local_handlers
        }

    def handle_all(self, req):
        print('[*] in handle all')
        stage, handler = self.local_handlers[req.request]
        response = self.get_mutation(stage=stage)
        if response is None:
            response = handler(req)
        self.app.send_on_endpoint(0, response)
        # self.supported()

    def handle_get_report(self, req):
        # response = b'\xff' * req.length
        response = b''
        return response

    def handle_get_idle(self, req):
        return b''

    def handle_set_report(self, req):
        return b''

    def handle_set_idle(self, req):
        return b''


class USBKeyboardInterface(USBInterface):
    name = "USB keyboard interface"

    def __init__(self, app, verbose=0):
        descriptors = {
            USB.desc_type_hid: self.get_hid_descriptor,
            USB.desc_type_report: self.get_report_descriptor
        }

        endpoint = USBEndpoint(
            app=app,
            number=3,
            direction=USBEndpoint.direction_in,
            transfer_type=USBEndpoint.transfer_type_interrupt,
            sync_type=USBEndpoint.sync_type_none,
            usage_type=USBEndpoint.usage_type_data,
            max_packet_size=0x40,
            interval=10,
            handler=self.handle_buffer_available
        )

        # TODO: un-hardcode string index (last arg before "verbose")
        super(USBKeyboardInterface, self).__init__(
            app=app,
            interface_number=0,
            interface_alternate=0,
            interface_class=3,
            interface_subclass=0,
            interface_protocol=0,
            interface_string_index=0,
            verbose=verbose,
            endpoints=[endpoint],
            descriptors=descriptors
        )

        self.device_class = USBKeyboardClass(app, verbose)
        self.device_class.set_interface(self)

        empty_preamble = [0x00] * 10
        text = [0x0f, 0x00, 0x16, 0x00, 0x28, 0x00]
        # text = []

        self.keys = [chr(x) for x in empty_preamble + text]

    @mutable('hid_descriptor')
    def get_hid_descriptor(self, *args, **kwargs):
        report_descriptor = self.get_report_descriptor()
        bDescriptorType = b'\x21'  # HID
        bcdHID = b'\x10\x01'
        bCountryCode = b'\x00'
        bNumDescriptors = b'\x01'
        bDescriptorType2 = b'\x22'  # REPORT
        desclen = len(report_descriptor)
        wDescriptorLength = pack('<H', desclen)
        hid_descriptor = (
            bDescriptorType +
            bcdHID +
            bCountryCode +
            bNumDescriptors +
            bDescriptorType2 +
            wDescriptorLength
        )
        bLength = bytes([len(hid_descriptor) + 1])
        hid_descriptor = bLength + hid_descriptor
        return hid_descriptor

    @mutable('hid_report_descriptor')
    def get_report_descriptor(self, *args, **kwargs):
        usage_page_generic_desktop_controls = b'\x05\x01'
        # usage_page_generic_desktop_controls = b'\xb1\x01'
        usage_keyboard = b'\x09\x06'
        collection_application = b'\xA1\x01'
        usage_page_keyboard = b'\x05\x07'
        usage_minimum1 = b'\x19\xE0'
        usage_maximum1 = b'\x29\xE7'
        logical_minimum1 = b'\x15\x00'
        logical_maximum1 = b'\x25\x01'
        report_size1 = b'\x75\x01'
        report_count1 = b'\x95\x08'
        input_data_variable_absolute_bitfield = b'\x81\x02'
        report_count2 = b'\x95\x01'
        report_size2 = b'\x75\x08'
        input_constant_array_absolute_bitfield = b'\x81\x01'
        usage_minimum2 = b'\x19\x00'
        usage_maximum2 = b'\x29\x65'
        logical_minimum2 = b'\x15\x00'
        logical_maximum2 = b'\x25\x65'
        report_size3 = b'\x75\x08'
        report_count3 = b'\x95\x01'
        input_data_array_absolute_bitfield = b'\x81\x00'
        end_collection = b'\xc0'

        report_descriptor = (
            usage_page_generic_desktop_controls +
            usage_keyboard +
            collection_application +
            usage_page_keyboard +
            usage_minimum1 +
            usage_maximum1 +
            logical_minimum1 +
            logical_maximum1 +
            report_size1 +
            report_count1 +
            input_data_variable_absolute_bitfield +
            report_count2 +
            report_size2 +
            input_constant_array_absolute_bitfield +
            usage_minimum2 +
            usage_maximum2 +
            logical_minimum2 +
            logical_maximum2 +
            report_size3 +
            report_count3 +
            input_data_array_absolute_bitfield +
            end_collection
        )
        return report_descriptor

    def handle_buffer_available(self):
        self.supported()
        if self.keys:
            letter = self.keys.pop(0)
            self.type_letter(letter)

    def type_letter(self, letter, modifiers=0):
        data = bytes([0, 0, ord(letter)])

        if self.verbose > 2:
            print(self.name, "sending keypress 0x%02x" % ord(letter))

        self.configuration.device.app.send_on_endpoint(3, data)


class USBKeyboardDevice(USBDevice):
    name = "USB keyboard device"

    def __init__(self, app, vid, pid, rev, verbose=0, **kwargs):
        interface = USBKeyboardInterface(app, verbose=verbose)
        config = USBConfiguration(
            app=app,
            configuration_index=1,
            configuration_string="Emulated Keyboard",
            interfaces=[interface]
        )
        super(USBKeyboardDevice, self).__init__(
            app=app,
            device_class=0,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=vid,
            product_id=pid,
            device_rev=rev,
            manufacturer_string="Dell",
            product_string="Dell USB Entry Keyboard",
            serial_number_string="00001",
            configurations=[config],
            descriptors={},
            verbose=verbose
        )
