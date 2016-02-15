# USBCDC.py
#
# Contains class definitions to implement a USB CDC device.

'''
.. todo:: see here re-enpoints <http://janaxelson.com/usb_virtual_com_port.htm>_
'''
from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBCSInterface import *
from USBEndpoint import *
from USBCSEndpoint import *
from .wrappers import mutable


class USBCDCClass(USBClass):
    name = "USB CDC class"

    def setup_request_handlers(self):
        self.local_responses = {
            0x22: ('cdc_set_control_line_state', b''),
            0x20: ('cdc_set_line_coding', b'')
        }
        self.request_handlers = {
            x: self.handle_all for x in self.local_responses
        }

    def handle_all(self, req):
        stage, default_response = self.local_responses[req.request]
        response = self.get_mutation(stage=stage)
        if response is None:
            response = default_response
        self.app.send_on_endpoint(0, response)
        self.supported()


class USBCDCInterface(USBInterface):
    name = "USB CDC interface"

    def __init__(self, int_num, maxusb_app, usbclass, sub, proto, verbose=0):
        self.maxusb_app = maxusb_app
        self.int_num = int_num
        descriptors = {}
        cs_config1 = [
            0x00,  # Header Functional Descriptor
            0x1001,  # bcdCDC
        ]

        bmCapabilities = 0x03
        bDataInterface = 0x01

        cs_config2 = [
            0x01,  # Call Management Functional Descriptor
            bmCapabilities,
            bDataInterface
        ]

        bmCapabilities = 0x06

        cs_config3 = [
            0x02,  # Abstract Control Management Functional Descriptor
            bmCapabilities
        ]

        bControlInterface = 0
        bSubordinateInterface0 = 1

        cs_config4 = [
            0x06,  # Union Functional Descriptor
            bControlInterface,
            bSubordinateInterface0
        ]

        cs_interfaces0 = [
            USBCSInterface(maxusb_app, cs_config1, 2, 2, 1),
            USBCSInterface(maxusb_app, cs_config2, 2, 2, 1),
            USBCSInterface(maxusb_app, cs_config3, 2, 2, 1),
            USBCSInterface(maxusb_app, cs_config4, 2, 2, 1)
        ]

        cs_interfaces1 = []

        endpoints0 = [
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=0x83,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_interrupt,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x2000,
                interval=0xff,
                handler=None
            )
        ]

        endpoints1 = [
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=0x81,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x2000,
                interval=0x00,
                handler=None
            ),
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=0x02,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x2000,
                interval=0x00,
                handler=self.handle_data_available
            )
        ]

        if self.int_num == 0:
                endpoints = endpoints0
                cs_interfaces = cs_interfaces0

        elif self.int_num == 1:
                endpoints = endpoints1
                cs_interfaces = cs_interfaces1

        # TODO: un-hardcode string index (last arg before "verbose")
        super(USBCDCInterface, self).__init__(
                maxusb_app=maxusb_app,
                interface_number=self.int_num,
                interface_alternate=0,
                interface_class=usbclass,
                interface_subclass=sub,
                interface_protocol=proto,
                interface_string_index=0,
                verbose=verbose,
                endpoints=endpoints,
                descriptors=descriptors,
                cs_interfaces=cs_interfaces
        )

        self.device_class = USBCDCClass(maxusb_app)
        self.device_class.set_interface(self)

    @mutable('cdc_handle_data_available')
    def handle_data_available(self, data):
        if self.verbose > 0:
            print(self.name, "handling", len(data), "bytes of audio data")


class USBCDCDevice(USBDevice):
    name = "USB CDC device"

    def __init__(self, maxusb_app, vid, pid, rev, verbose=0, **kwargs):
        interface0 = USBCDCInterface(0, maxusb_app, 0x02, 0x02, 0x01, verbose=verbose)
        interface1 = USBCDCInterface(1, maxusb_app, 0x0a, 0x00, 0x00, verbose=verbose)

        config = USBConfiguration(
            maxusb_app=maxusb_app,
            configuration_index=1,
            configuration_string="Emulated CDC",
            interfaces=[interface0, interface1]
        )

        super(USBCDCDevice, self).__init__(
            maxusb_app=maxusb_app,
            device_class=2,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=vid,
            product_id=pid,
            device_rev=rev,
            manufacturer_string="Vendor",
            product_string="Product",
            serial_number_string="Serial",
            configurations=[config],
            descriptors={},
            verbose=verbose
        )
