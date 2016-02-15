# USBMassStorage.py
#
# Contains class definitions to implement a USB mass storage device.
'''
.. todo::

    Something to check all over the place - little/big endianess of data
'''
from mmap import mmap
import os
from struct import pack, unpack
from enum import IntEnum

from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *
from USBClass import *
from util import *
from .wrappers import mutable


class ScsiCmds(IntEnum):
    TEST_UNIT_READY = 0x00
    REQUEST_SENSE = 0x03
    READ_6 = 0x08
    WRITE_6 = 0x0A
    INQUIRY = 0x12
    MODE_SENSE_6 = 0x1A
    SEND_DIAGNOSTIC = 0x1D
    PREVENT_ALLOW_MEDIUM_REMOVAL = 0x1E
    READ_FORMAT_CAPACITIES = 0x23
    READ_CAPACITY_10 = 0x25
    READ_10 = 0x28
    WRITE_10 = 0x2A
    VERIFY_10 = 0x2F
    SYNCHRONIZE_CACHE = 0x35
    MODE_SENSE_10 = 0x5A


class ScsiSenseKeys(IntEnum):
    GOOD = 0x00
    RECOVERED_ERROR = 0x01
    NOT_READY = 0x02
    MEDIUM_ERROR = 0x03
    HARDWARE_ERROR = 0x04
    ILLEGAL_REQUEST = 0x05
    UNIT_ATTENTION = 0x06
    DATA_PROTECT = 0x07
    BLANK_CHECK = 0x08
    VENDOR_SPECIFIC = 0x09
    COPY_ABORTED = 0x0A
    ABORTED_COMMAND = 0x0B
    VOLUME_OVERFLOW = 0x0D
    MISCOMPARE = 0x0E


class USBMassStorageClass(USBClass):
    name = "USB mass storage class"

    def setup_request_handlers(self):
        self.request_handlers = {
            0xFF: self.handle_bulk_only_mass_storage_reset_request,
            0xFE: self.handle_get_max_lun_request
        }

    def handle_bulk_only_mass_storage_reset_request(self, req):
        self.interface.configuration.device.maxusb_app.send_on_endpoint(0, b'')

    def handle_get_max_lun_request(self, req):
        self.interface.configuration.device.maxusb_app.send_on_endpoint(0, b'\x00')


class USBMassStorageInterface(USBInterface):
    '''
    .. todo:: all handlers - should be more dynamic??
    '''
    name = "USB mass storage interface"

    def __init__(self, maxusb_app, disk_image, usbclass, sub, proto, verbose=0):
        self.disk_image = disk_image
        self.maxusb_app = maxusb_app
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

        # TODO: un-hardcode string index (last arg before "verbose")
        super(USBMassStorageInterface, self).__init__(
                maxusb_app=maxusb_app,
                interface_number=0,
                interface_alternate=0,
                interface_class=usbclass,
                interface_subclass=sub,
                interface_protocol=proto,
                interface_string_index=0,
                verbose=verbose,
                endpoints=endpoints,
                descriptors=descriptors
        )

        self.device_class = USBMassStorageClass(maxusb_app, verbose)
        self.device_class.set_interface(self)

        self.is_write_in_progress = False
        self.write_cbw = None
        self.write_base_lba = 0
        self.write_length = 0
        self.write_data = b''

        self.format_capacities_list = [
            (0x00001000, 0x00, 0x000200),
        ]

        self.operations = {
            ScsiCmds.INQUIRY: self.handle_inquiry,
            ScsiCmds.REQUEST_SENSE: self.handle_request_sense,
            ScsiCmds.TEST_UNIT_READY: self.handle_test_unit_ready,
            ScsiCmds.READ_CAPACITY_10: self.handle_read_capacity_10,
            ScsiCmds.SEND_DIAGNOSTIC: self.handle_send_diagnostic,
            ScsiCmds.PREVENT_ALLOW_MEDIUM_REMOVAL: self.handle_prevent_allow_medium_removal,
            ScsiCmds.WRITE_10: self.handle_write_10,
            ScsiCmds.READ_10: self.handle_read_10,
            ScsiCmds.WRITE_6: self.handle_write_6,
            ScsiCmds.READ_6: self.handle_read_6,
            ScsiCmds.VERIFY_10: self.handle_verify_10,
            ScsiCmds.MODE_SENSE_6: self.handle_mode_sense_6,
            ScsiCmds.MODE_SENSE_10: self.handle_mode_sense_10,
            ScsiCmds.READ_FORMAT_CAPACITIES: self.handle_read_format_capacities,
            ScsiCmds.SYNCHRONIZE_CACHE: self.handle_synchronize_cache,
        }

    @mutable('scsi_inquiry_response')
    def handle_inquiry(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Inquiry, data", bytes_as_hex(cbw.cb[1:]))
        peripheral = 0x00  # SBC
        RMB = 0x80  # Removable
        version = 0x00
        response_data_format = 0x01
        config = (0x00, 0x00, 0x00)
        vendor_id = b'PNY     '
        product_id = b'USB 2.0 FD      '
        product_revision_level = b'8.02'

        part1 = pack('BBBB', peripheral, RMB, version, response_data_format)
        part2 = pack('BBB', *config) + vendor_id + product_id + product_revision_level
        length = pack('B', len(part2))
        response = part1 + length + part2
        return response

    @mutable('scsi_request_sense_response')
    def handle_request_sense(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Request Sense, data", bytes_as_hex(cbw.cb[1:]))
        response_code = 0x70
        valid = 0x00
        filemark = 0x06
        information = 0x00000000
        command_info = 0x00000000
        additional_sense_code = 0x3a
        additional_sens_code_qualifier = 0x00
        field_replacement_unti_code = 0x00
        sense_key_specific = b'\x00\x00\x00'

        part1 = pack('<BBBI', response_code, valid, filemark, information)
        part2 = pack(
            '<IBBB',
            command_info,
            additional_sense_code,
            additional_sens_code_qualifier,
            field_replacement_unti_code
        )
        part2 += sense_key_specific
        length = pack('B', len(part2))
        response = part1 + length + part2
        return response

    @mutable('scsi_test_unit_ready_response')
    def handle_test_unit_ready(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Test Unit Ready")

    @mutable('scsi_read_capacity_10_response')
    def handle_read_capacity_10(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Read Capacity, data", bytes_as_hex(cbw.cb[1:]))
        lastlba = self.disk_image.get_sector_count()
        logical_block_address = pack('<I', lastlba)
        length = 0x00020000
        response = logical_block_address + pack('<I', length)
        return response

    @mutable('scsi_send_diagnostic_response')
    def handle_send_diagnostic(self, cbw):
        raise NotImplementedError('yet...')

    @mutable('scsi_prevent_allow_medium_removal_response')
    def handle_prevent_allow_medium_removal(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Prevent/Allow Removal")

    @mutable('scsi_write_10_response')
    def handle_write_10(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Write (10), data", bytes_as_hex(cbw.cb[1:]))

        base_lba = unpack('>I', cbw.cb[1:5])[0]
        num_blocks = unpack('>H', cbw.cb[7:9])[0]

        if self.verbose > 0:
            print(self.name, "got SCSI Write (10), lba", base_lba, "+",  num_blocks, "block(s)")

        # save for later
        self.write_cbw = cbw
        self.write_base_lba = base_lba
        self.write_length = num_blocks * self.disk_image.block_size
        self.is_write_in_progress = True

    @mutable('scsi_read_10_response')
    def handle_read_10(self, cbw):
        '''
        .. todo:: do we want to fuzz each message in the inner loop separatley?
        '''
        if self.maxusb_app.mode == 4:
            self.maxusb_app.stop = True

        base_lba = unpack('>I', cbw.cb[1:5])[0]
        num_blocks = unpack('>H', cbw.cb[7:9])[0]

        if self.verbose > 0:
            print(self.name, "got SCSI Read (10), lba", base_lba, "+", num_blocks, "block(s)")

        # Note that here we send the data directly rather than putting
        # something in 'response' and letting the end of the switch send
        for block_num in range(num_blocks):
            data = self.disk_image.get_sector_data(base_lba + block_num)
            self.configuration.device.maxusb_app.send_on_endpoint(3, data)

    @mutable('scsi_write_6_response')
    def handle_write_6(self, cbw):
        raise NotImplementedError('yet...')

    @mutable('scsi_read_6_response')
    def handle_read_6(self, cbw):
        raise NotImplementedError('yet...')

    @mutable('scsi_verify_10_response')
    def handle_verify_10(self, cbw):
        raise NotImplementedError('yet...')

    def handle_scsi_mode_sense(self, cbw):
        page = cbw.cb[2] & 0x3f

        if self.verbose > 0:
            print(self.name, "got SCSI Mode Sense, page code 0x%02x" % page)

        if page == 0x1c:
            medium_type = 0x00
            device_specific_param = 0x00
            block_descriptor_len = 0x00
            mode_page_1c = b'\x1c\x06\x00\x05\x00\x00\x00\x00'
            body = pack('BBB', medium_type, device_specific_param, block_descriptor_len)
            body += mode_page_1c
            length = pack('<B', len(body))
            response = length + body

        elif page == 0x3f:
            length = 0x45  # .. todo:: this seems awefully wrong
            medium_type = 0x00
            device_specific_param = 0x00
            block_descriptor_len = 0x08
            mode_page = 0x00000000
            response = pack('<BBBBI', length, medium_type, device_specific_param, block_descriptor_len, mode_page)
        else:
            length = 0x07
            medium_type = 0x00
            device_specific_param = 0x00
            block_descriptor_len = 0x00
            mode_page = 0x00000000
            response = pack('<BBBBI', length, medium_type, device_specific_param, block_descriptor_len, mode_page)
        return response

    @mutable('scsi_mode_sense_6_response')
    def handle_mode_sense_6(self, cbw):
        return self.handle_scsi_mode_sense(cbw)

    @mutable('scsi_mode_sense_10_response')
    def handle_mode_sense_10(self, cbw):
        return self.handle_scsi_mode_sense(cbw)

    @mutable('scsi_read_format_capacities')
    def handle_read_format_capacities(self, cbw):
        if self.verbose > 0:
            print(self.name, "got SCSI Read Format Capacity")
        response = pack('>I', len(self.format_capacities_list) * 8)
        for block_num, desc_code, block_len in self.format_capacities_list:
            response += pack('>IB', block_num, desc_code)
            response += pack('>I', block_len)[1:]
        return response

    def handle_synchronize_cache(self, cbw):
        if self.verbose > 0:
                print(self.name, "got Synchronize Cache (10)")

    def handle_data_available(self, data):
        if self.verbose > 0:
            print(self.name, "handling", len(data), "bytes of SCSI data")
        self.supported()
        cbw = CommandBlockWrapper(data)
        opcode = cbw.cb[0]
        status = 0              # default to success
        response = None         # with no response data

        if self.maxusb_app.server_running:
            try:
                self.maxusb_app.netserver_from_endpoint_sd.send(data)
            except:
                print ("Error: No network client connected")

            while True:
                if len(self.maxusb_app.reply_buffer) > 0:
                    self.maxusb_app.send_on_endpoint(3, self.maxusb_app.reply_buffer)
                    self.maxusb_app.reply_buffer = ""
                    break

        elif self.is_write_in_progress:
            if self.verbose > 0:
                print(self.name, "got", len(data), "bytes of SCSI write data")

            self.write_data += data

            if len(self.write_data) < self.write_length:
                # more yet to read, don't send the CSW
                return

            self.disk_image.put_sector_data(self.write_base_lba, self.write_data)
            cbw = self.write_cbw

            self.is_write_in_progress = False
            self.write_data = b''

        if opcode in self.operations:
            handler = self.operations[opcode]
            try:
                response = handler(cbw)
                if opcode == ScsiCmds.WRITE_10:
                    # because we need to snarf up the data from wire before we reply
                    # with the CSW
                    return
            except NotImplementedError as ex:
                print('Command %02x is not implemented yet (though it should be supported...)' % opcode)
                raise ex
        else:
            if self.verbose > 0:
                print(self.name, "received unsupported SCSI opcode 0x%x" % opcode)
            status = 0x02   # command failed
            if cbw.data_transfer_length > 0:
                response = bytes([0] * cbw.data_transfer_length)

        if response and not self.maxusb_app.server_running:
            if self.verbose > 2:
                print(self.name, "responding with", len(response), "bytes:", bytes_as_hex(response))
            self.configuration.device.maxusb_app.send_on_endpoint(3, response)

        csw = bytes([
            ord('U'), ord('S'), ord('B'), ord('S'),
            cbw.tag[0], cbw.tag[1], cbw.tag[2], cbw.tag[3],
            0x00, 0x00, 0x00, 0x00,
            status
        ])

        if self.verbose > 3:
            print(self.name, "responding with status =", status)

        self.configuration.device.maxusb_app.send_on_endpoint(3, csw)


class DiskImage:
    def __init__(self, filename, block_size):
        self.filename = filename
        self.block_size = block_size

        statinfo = os.stat(self.filename)
        self.size = statinfo.st_size

        self.file = open(self.filename, 'r+b')
        self.image = mmap(self.file.fileno(), 0)

    def close(self):
        self.image.flush()
        self.image.close()

    def get_sector_count(self):
        return int(self.size / self.block_size) - 1

    def get_sector_data(self, address):
        block_start = address * self.block_size
        block_end = (address + 1) * self.block_size   # slices are NON-inclusive

        return self.image[block_start:block_end]

    def put_sector_data(self, address, data):
        block_start = address * self.block_size
        block_end = (address + 1) * self.block_size   # slices are NON-inclusive

        self.image[block_start:block_end] = data[:self.block_size]
        self.image.flush()


class CommandBlockWrapper:
    def __init__(self, bytestring):
        self.signature = bytestring[0:4]
        self.tag = bytestring[4:8]
        self.data_transfer_length = (
            bytestring[8] |
            bytestring[9] << 8 |
            bytestring[10] << 16 |
            bytestring[11] << 24
        )
        self.flags = int(bytestring[12])
        self.lun = int(bytestring[13] & 0x0f)
        self.cb_length = int(bytestring[14] & 0x1f)
        # self.cb = bytestring[15:15+self.cb_length]
        self.cb = bytestring[15:]

    def __str__(self):
        s = "sig: " + bytes_as_hex(self.signature) + "\n"
        s += "tag: " + bytes_as_hex(self.tag) + "\n"
        s += "data transfer len: " + str(self.data_transfer_length) + "\n"
        s += "flags: " + str(self.flags) + "\n"
        s += "lun: " + str(self.lun) + "\n"
        s += "command block len: " + str(self.cb_length) + "\n"
        s += "command block: " + bytes_as_hex(self.cb) + "\n"

        return s


class USBMassStorageDevice(USBDevice):
    name = "USB mass storage device"

    def __init__(self, maxusb_app, vid, pid, rev, usbclass, subclass, proto, disk_image_filename='stick.img', verbose=0):
        self.disk_image = DiskImage(disk_image_filename, 512)
        interface = USBMassStorageInterface(maxusb_app, self.disk_image, usbclass, subclass, proto, verbose=verbose)

        config = USBConfiguration(
                maxusb_app=maxusb_app,
                configuration_index=1,
                configuration_string="MassStorage config",
                interfaces=[interface]
        )

        super(USBMassStorageDevice, self).__init__(
                maxusb_app=maxusb_app,
                device_class=0,
                device_subclass=0,
                protocol_rel_num=0,
                max_packet_size_ep0=64,
                vendor_id=vid,
                product_id=pid,
                device_rev=rev,
                manufacturer_string="PNY",
                product_string="USB 2.0 FD",
                serial_number_string="4731020ef1914da9",
                configurations=[config],
                verbose=verbose
        )

    def disconnect(self):
        self.disk_image.close()
        USBDevice.disconnect(self)

