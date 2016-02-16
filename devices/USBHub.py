# USBHub.py
#
# Contains class definitions to implement a USB hub.
from struct import pack
from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *
from .wrappers import mutable


class USBHubClass(USBClass):
    name = "USB hub class"

    def setup_request_handlers(self):
        self.local_handlers = {
            0x00: ('hub_get_hub_status', self.handle_get_hub_status_request),
            0x03: ('hub_set_port_feature', self.handle_set_port_feature_request),
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
        self.supported()

    def handle_get_hub_status_request(self, req):
        return b'\x61\x61\x61\x61'

    def handle_set_port_feature_request(self, req):
        return b''


class USBHubInterface(USBInterface):
    name = "USB hub interface"

    def __init__(self, app, verbose=0):
        descriptors = {
                USB.desc_type_hub: self.get_hub_descriptor
        }

        endpoint = USBEndpoint(
                app=app,
                number=0x2,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_interrupt,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=16384,
                interval=0x0c,
                handler=self.handle_buffer_available
        )

        # TODO: un-hardcode string index (last arg before "verbose")
        super(USBHubInterface, self).__init__(
            app=app,
            interface_number=0,          # interface number
            interface_alternate=0,          # alternate setting
            interface_class=9,          # 3 interface class
            interface_subclass=0,          # 0 subclass
            interface_protocol=0,          # 0 protocol
            interface_string_index=0,          # string index
            verbose=verbose,
            endpoints=[endpoint],
            descriptors=descriptors
        )

        self.device_class = USBHubClass(app)
        self.device_class.set_interface(self)

    @mutable('hub_descriptor')
    def get_hub_descriptor(self, **kwargs):
        bLength = 9
        bDescriptorType = 0x29
        bNbrPorts = 4
        wHubCharacteristics = 0xe000
        bPwrOn2PwrGood = 0x32
        bHubContrCurrent = 0x64
        DeviceRemovable = 0
        PortPwrCtrlMask = 0xff

        return pack(
            '<BBBHBBBB',
            bLength,
            bDescriptorType,
            bNbrPorts,
            wHubCharacteristics,
            bPwrOn2PwrGood,
            bHubContrCurrent,
            DeviceRemovable,
            PortPwrCtrlMask
        )

    @mutable('hub_buffer_available_response')
    def handle_buffer_available(self):
        return


class USBHubDevice(USBDevice):
    name = "USB hub device"

    def __init__(self, app, vid, pid, rev, verbose=0, **kwargs):
        interface = USBHubInterface(app, verbose=verbose)

        config = USBConfiguration(
            app=app,
            configuration_index=1,
            configuration_string="Emulated Hub",
            interfaces=[interface]
        )

        super(USBHubDevice, self).__init__(
            app=app,
            device_class=9,
            device_subclass=0,
            protocol_rel_num=1,
            max_packet_size_ep0=64,
            vendor_id=vid,
            product_id=pid,
            device_rev=rev,
            manufacturer_string="Genesys Logic, Inc",
            product_string="USB2.0 Hub",
            serial_number_string="1234",
            configurations=[config],
            descriptors={},
            verbose=verbose
        )
