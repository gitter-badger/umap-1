# USBFtdi.py
#
# Contains class definitions to implement a USB FTDI chip.

from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *
from USBVendor import *
from util import *


class USBFtdiVendor(USBVendor):
    name = "USB FTDI vendor"

    def setup_request_handlers(self):
        self.local_handlers = {
            0: ('ftdi_reset_response', self.handle_reset_request),
            1: ('ftdi_modem_ctrl_response', self.handle_modem_ctrl_request),
            2: ('ftdi_set_flow_ctrl_response', self.handle_set_flow_ctrl_request),
            3: ('ftdi_set_baud_rate_response', self.handle_set_baud_rate_request),
            4: ('ftdi_set_data_response', self.handle_set_data_request),
            5: ('ftdi_get_status_response', self.handle_get_status_request),
            6: ('ftdi_set_event_char_response', self.handle_set_event_char_request),
            7: ('ftdi_set_error_char_response', self.handle_set_error_char_request),
            9: ('ftdi_set_latency_timer_response', self.handle_set_latency_timer_request),
            10: ('ftdi_get_latency_timer_response', self.handle_get_latency_timer_request),
        }
        self.request_handlers = {
            x: self.handle_all for x in self.local_handlers
        }

    def handle_all(self, req):
        stage, handler = self.local_handlers[req.request]
        response = self.get_mutation(stage=stage)
        if response is None:
            response = handler(req)
        self.app.send_on_endpoint(0, response)

    def handle_reset_request(self, req):
        if self.verbose > 0:
            print(self.name, "received reset request")

        return b''

    def handle_modem_ctrl_request(self, req):
        if self.verbose > 0:
            print(self.name, "received modem_ctrl request")
        dtr = req.value & 0x0001
        rts = (req.value & 0x0002) >> 1
        dtren = (req.value & 0x0100) >> 8
        rtsen = (req.value & 0x0200) >> 9
        if dtren:
            print("DTR is enabled, value", dtr)
        if rtsen:
            print("RTS is enabled, value", rts)
        return b''

    def handle_set_flow_ctrl_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_flow_ctrl request")
        if req.value == 0x000:
            print("SET_FLOW_CTRL to no handshaking")
        if req.value & 0x0001:
            print("SET_FLOW_CTRL for RTS/CTS handshaking")
        if req.value & 0x0002:
            print("SET_FLOW_CTRL for DTR/DSR handshaking")
        if req.value & 0x0004:
            print("SET_FLOW_CTRL for XON/XOFF handshaking")
        return b''

    def handle_set_baud_rate_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_baud_rate request")

        dtr = req.value & 0x0001
        print("baud rate set to", dtr)
        return b''

    def handle_set_data_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_data request")
        return b''

    def handle_get_status_request(self, req):
        if self.verbose > 0:
            print(self.name, "received get_status request")
        return b''

    def handle_set_event_char_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_event_char request")
        return b''

    def handle_set_error_char_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_error_char request")
        return b''

    def handle_set_latency_timer_request(self, req):
        if self.verbose > 0:
            print(self.name, "received set_latency_timer request")
        return b''

    def handle_get_latency_timer_request(self, req):
        if self.verbose > 0:
            print(self.name, "received get_latency_timer request")
        return b'\x01'


class USBFtdiInterface(USBInterface):
    name = "USB FTDI interface"

    def __init__(self, int_num, maxusb_app, verbose=0):
        descriptors = {}

        endpoints = [
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=1,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=16384,
                interval=0,
                handler=self.handle_data_available
            ),
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=3,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=16384,
                interval=0,
                handler=None
            )
        ]

        super(USBFtdiInterface, self).__init__(
            maxusb_app=maxusb_app,
            interface_number=int_num,
            interface_alternate=0,
            interface_class=0xff,
            interface_subclass=0xff,
            interface_protocol=0xff,
            interface_string_index=0,
            verbose=verbose,
            endpoints=endpoints,
            descriptors=descriptors
        )

    def handle_data_available(self, data):
        st = data[1:]
        if self.verbose > 0:
            print(self.name, "received string", st)
        st = st.replace(b'\r', b'\r\n')
        reply = b'\x01\x00' + st
        self.configuration.device.maxusb_app.send_on_endpoint(3, reply)


class USBFtdiDevice(USBDevice):
    name = "USB FTDI device"

    def __init__(self, maxusb_app, verbose=0, **kwargs):
        interface = USBFtdiInterface(0, maxusb_app, verbose=verbose)

        config = USBConfiguration(
            maxusb_app=maxusb_app,
            configuration_index=1,
            configuration_string="FTDI config",
            interfaces=[interface]
        )

        super(USBFtdiDevice, self).__init__(
                maxusb_app=maxusb_app,
                device_class=0,
                device_subclass=0,
                protocol_rel_num=0,
                max_packet_size_ep0=64,
                vendor_id=0x0403,  # 0403 vendor id: FTDI
                product_id=0x6001,  # 6001 product id: FT232 USB-Serial (UART) IC
                device_rev=0x0001,  # 0001 device revision
                manufacturer_string="GoodFET",
                product_string="FTDI Emulator",
                serial_number_string="S/N3420E",
                configurations=[config],
                verbose=verbose
        )

        self.device_vendor = USBFtdiVendor(app=maxusb_app)
        self.device_vendor.set_device(self)
