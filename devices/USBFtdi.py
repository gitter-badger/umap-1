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

    def setup_local_handlers(self):
        self.local_handlers = {
            0: self.handle_reset,
            1: self.handle_modem_ctrl,
            2: self.handle_set_flow_ctrl,
            3: self.handle_set_baud_rate,
            4: self.handle_set_data,
            5: self.handle_get_status,
            6: self.handle_set_event_char,
            7: self.handle_set_error_char,
            9: self.handle_set_latency_timer,
            10: self.handle_get_latency_timer,
        }

    @mutable('ftdi_reset_response')
    def handle_reset(self, req):
        if self.verbose > 0:
            print(self.name, "received reset request")

        return b''

    @mutable('ftdi_modem_ctrl_response')
    def handle_modem_ctrl(self, req):
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

    @mutable('ftdi_set_flow_ctrl_response')
    def handle_set_flow_ctrl(self, req):
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

    @mutable('ftdi_set_baud_rate_response')
    def handle_set_baud_rate(self, req):
        if self.verbose > 0:
            print(self.name, "received set_baud_rate request")

        dtr = req.value & 0x0001
        print("baud rate set to", dtr)
        return b''

    @mutable('ftdi_set_data_response')
    def handle_set_data(self, req):
        if self.verbose > 0:
            print(self.name, "received set_data request")
        return b''

    @mutable('ftdi_get_status_response')
    def handle_get_status(self, req):
        if self.verbose > 0:
            print(self.name, "received get_status request")
        return b''

    @mutable('ftdi_set_event_char_response')
    def handle_set_event_char(self, req):
        if self.verbose > 0:
            print(self.name, "received set_event_char request")
        return b''

    @mutable('ftdi_set_error_char_response')
    def handle_set_error_char(self, req):
        if self.verbose > 0:
            print(self.name, "received set_error_char request")
        return b''

    @mutable('ftdi_set_latency_timer_response')
    def handle_set_latency_timer(self, req):
        if self.verbose > 0:
            print(self.name, "received set_latency_timer request")
        return b''

    @mutable('ftdi_get_latency_timer_response')
    def handle_get_latency_timer(self, req):
        if self.verbose > 0:
            print(self.name, "received get_latency_timer request")
        return b'\x01'


class USBFtdiInterface(USBInterface):
    name = "USB FTDI interface"

    def __init__(self, int_num, app, verbose=0):
        descriptors = {}

        endpoints = [
            USBEndpoint(
                app=app,
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
                app=app,
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
            app=app,
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
        self.configuration.device.app.send_on_endpoint(3, reply)


class USBFtdiDevice(USBDevice):
    name = "USB FTDI device"

    def __init__(self, app, verbose=0, **kwargs):
        interface = USBFtdiInterface(0, app, verbose=verbose)

        config = USBConfiguration(
            app=app,
            configuration_index=1,
            configuration_string="FTDI config",
            interfaces=[interface]
        )

        super(USBFtdiDevice, self).__init__(
                app=app,
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

        self.device_vendor = USBFtdiVendor(app=app)
        self.device_vendor.set_device(self)
