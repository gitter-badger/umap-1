# USBMtp.py
#
# Contains class definitions to implement a USB keyboard.

from binascii import unhexlify, hexlify
from enum import IntEnum
import struct
# from USB import *
from USBDevice import USBDevice
from USBConfiguration import USBConfiguration
from USBInterface import USBInterface
from USBEndpoint import USBEndpoint
from USBVendor import USBVendor
from .wrappers import mutable


class MtpDataCodeTypes(IntEnum):
    PTP_OPERATION = 0x1000
    PTP_RESPONSE = 0x2000
    PTP_OBJECT_FORMAT = 0x3000
    PTP_EVENT = 0x4000
    PTP_DEVICE_PROP = 0x5000
    VENDOR_EXTENSION_OPERATION = 0x9000
    MTP_OPERATION = 0x9800
    VENDOR_EXTENSION_RESPONSE = 0xA000
    MTP_RESPONSE = 0xA800
    VENDOR_EXTENSION_OBJECT_FORMAT = 0xB000
    MTP_OBJECT_FORMAT = 0xB800
    VENDOR_EXTENSION_EVENT = 0xC000
    MTP_EVENT = 0xC800
    VENDOR_EXTENSION_DEVICE_PROP = 0xD000
    MTP_DEVICE_PROP = 0xD400
    VENDOR_EXTENSION_OBJECT_PROP = 0xD800
    MTP_OBJECT_PROP = 0xDC00


class MtpResponseCodes(IntEnum):
    UNDEFINED = 0x2000
    OK = 0x2001
    GENERAL_ERROR = 0x2002
    SESSION_NOT_OPEN = 0x2003
    INVALID_TRANSACTION_ID = 0x2004
    OPERATION_NOT_SUPPORTED = 0x2005
    PARAMETER_NOT_SUPPORTED = 0x2006
    INCOMPLETE_TRANSFER = 0x2007
    INVALID_STORAGE_ID = 0x2008
    INVALID_OBJECT_HANDLE = 0x2009
    DEVICE_PROP_NOT_SUPPORTED = 0x200A
    INVALID_OBJECT_FORMAT_CODE = 0x200B
    STORAGE_FULL = 0x200C
    OBJECT_WRITE_PROTECTED = 0x200D
    STORE_READ_ONLY = 0x200E
    ACCESS_DENIED = 0x200F
    NO_THUMBNAIL_PRESENT = 0x2010
    SELF_TEST_FAILED = 0x2011
    PARTIAL_DELETION = 0x2012
    STORE_NOT_AVAILABLE = 0x2013
    SPECIFICATION_BY_FORMAT_UNSUPPORTED = 0x2014
    NO_VALID_OBJECT_INFO = 0x2015
    INVALID_CODE_FORMAT = 0x2016
    UNKNOWN_VENDOR_CODE = 0x2017
    CAPTURE_ALREADY_TERMINATED = 0x2018
    DEVICE_BUSY = 0x2019
    INVALID_PARENT_OBJECT = 0x201A
    INVALID_DEVICE_PROP_FORMAT = 0x201B
    INVALID_DEVICE_PROP_VALUE = 0x201C
    INVALID_PARAMETER = 0x201D
    SESSION_ALREADY_OPEN = 0x201E
    TRANSACTION_CANCELLED = 0x201F
    SPECIFICATION_OF_DESTINATION_UNSUPPORTED = 0x2020
    INVALID_OBJECT_PROP_CODE = 0xA801
    INVALID_OBJECT_PROP_FORMAT = 0xA802
    INVALID_OBJECT_PROP_VALUE = 0xA803
    INVALID_OBJECT_REFERENCE = 0xA804
    GROUP_NOT_SUPPORTED = 0xA805
    INVALID_DATASET = 0xA806
    SPECIFICATION_BY_GROUP_UNSUPPORTED = 0xA807
    SPECIFICATION_BY_DEPTH_UNSUPPORTED = 0xA808
    OBJECT_TOO_LARGE = 0xA809
    OBJECT_PROP_NOT_SUPPORTED = 0xA80A


class MtpOperationDataCodes(IntEnum):
    GetDeviceInfo = 0x1001
    OpenSession = 0x1002
    CloseSession = 0x1003
    GetStorageIDs = 0x1004
    GetStorageInfo = 0x1005
    GetNumObjects = 0x1006
    GetObjectHandles = 0x1007
    GetObjectInfo = 0x1008
    GetObject = 0x1009
    GetThumb = 0x100A
    DeleteObject = 0x100B
    SendObjectInfo = 0x100C
    SendObject = 0x100D
    InitiateCapture = 0x100E
    FormatStore = 0x100F
    ResetDevice = 0x1010
    SelfTest = 0x1011
    SetObjectProtection = 0x1012
    PowerDown = 0x1013
    GetDevicePropDesc = 0x1014
    GetDevicePropValue = 0x1015
    SetDevicePropValue = 0x1016
    ResetDevicePropValue = 0x1017
    TerminateOpenCapture = 0x1018
    MoveObject = 0x1019
    CopyObject = 0x101A
    GetPartialObject = 0x101B
    InitiateOpenCapture = 0x101C
    GetObjectPropsSupported = 0x9801
    GetObjectPropDesc = 0x9802
    GetObjectPropValue = 0x9803
    SetObjectPropValue = 0x9804
    GetObjectReferences = 0x9810
    SetObjectReferences = 0x9811
    Skip = 0x9820


class MtpContainerTypes(IntEnum):
    Undefined = 0
    Command = 1
    Data = 2
    Response = 3
    Event = 4


class MtpStorageType(IntEnum):
    FIXED_ROM = 0x0001
    REMOVABLE_ROM = 0x0002
    FIXED_RAM = 0x0003
    REMOVABLE_RAM = 0x0004


class MtpFSType(IntEnum):
    FLAT = 0x0001
    HIERARCHICAL = 0x0002
    DCF = 0x0003


class MtpAccessCaps(IntEnum):
    READ_WRITE = 0x0000
    READ_ONLY_WITHOUT_DELETE = 0x0001
    READ_ONLY_WITH_DELETE = 0x0002


class MtpContainer(object):

    def __init__(self, data):
        (
            self.length,
            self.type,
            self.code,
            self.tid,
        ) = struct.unpack('<IHHI', data[:12])
        self.data = data[12:]


def MStr(s):
    '''
    .. todo:: 1 byte length, then unicode null-terminated string
    '''
    encoded = s  # should probably be some encoding...
    return struct.pack('<B', len(encoded)) + encoded


def MS8(i):
    return struct.pack('<B', i)


def MU8(i):
    return struct.pack('<B', i)


def MS16(i):
    return struct.pack('<H', i)


def MU16(i):
    return struct.pack('<H', i)


def MS32(i):
    return struct.pack('<I', i)


def MU32(i):
    return struct.pack('<I', i)


def MS64(i):
    return struct.pack('<Q', i)


def MU64(i):
    return struct.pack('<Q', i)


class MtpStorageInfo(object):

    def __init__(self, stype, fstype, access, max_cap, free_space_bytes, free_space_objs, desc, vid):
        self.stype = stype
        self.fstype = fstype
        self.access = access
        self.max_cap = max_cap
        self.free_space_bytes = free_space_bytes
        self.free_space_objs = free_space_objs
        self.desc = desc
        self.vid = vid

    def serialize(self):
        return (
            MU16(self.stype) +
            MU16(self.fstype) +
            MU16(self.access) +
            MU64(self.max_cap) +
            MU64(self.free_space_bytes) +
            MU32(self.free_space_objs) +
            MStr(self.desc) +
            MStr(self.vid)
        )


def mtp_response(container, status):
    tid = 0 if not container else container.tid
    return MU32(0xC) + MU16(MtpContainerTypes.Response) + MU16(status) + MU32(tid)


def mtp_error(container, status):
    return (None, mtp_response(container, status))


def mtp_data(container, data):
    return MU32(len(data) + 0xC) + MU16(MtpContainerTypes.Data) + MU16(container.code) + MU32(container.tid) + data


class MtpDevice(object):
    '''
    Simulate an MTP device.
    This class should handle the MTP traffic itself
    '''
    def __init__(self, app, verbose):
        self.app = app
        self.verbose = verbose
        self.session_data = {}
        self.resp_queue = []
        self.storages = {
            # fictitious storage ids ....
            0x00010002: MtpStorageInfo(
                MtpStorageType.FIXED_ROM, MtpFSType.HIERARCHICAL, MtpAccessCaps.READ_WRITE,
                100000000, 90000000, 0xffffffff, "storage 1", "0x00010002"),
            0x00010003: MtpStorageInfo(
                MtpStorageType.FIXED_ROM, MtpFSType.HIERARCHICAL, MtpAccessCaps.READ_WRITE,
                100000000, 90000000, 0xffffffff, "storage 2", "0x00010003"),
            0x00010004: MtpStorageInfo(
                MtpStorageType.FIXED_ROM, MtpFSType.HIERARCHICAL, MtpAccessCaps.READ_WRITE,
                100000000, 90000000, 0xffffffff, "storage 3", "0x00010004"),
        }
        self.command_handlers = {
            MtpOperationDataCodes.GetDeviceInfo: self.op_GetDeviceInfo,
            MtpOperationDataCodes.OpenSession: self.op_OpenSession,
            MtpOperationDataCodes.CloseSession: self.op_CloseSession,
            MtpOperationDataCodes.GetStorageIDs: self.op_GetStorageIDs,
            MtpOperationDataCodes.GetStorageInfo: self.op_GetStorageInfo,
            # MtpOperationDataCodes.GetNumObjects: self.op_GetNumObjects,
            # MtpOperationDataCodes.GetObjectHandles: self.op_GetObjectHandles,
            # MtpOperationDataCodes.GetObjectInfo: self.op_GetObjectInfo,
            # MtpOperationDataCodes.GetObject: self.op_GetObject,
            # MtpOperationDataCodes.GetThumb: self.op_GetThumb,
            # MtpOperationDataCodes.DeleteObject: self.op_DeleteObject,
            # MtpOperationDataCodes.SendObjectInfo: self.op_SendObjectInfo,
            # MtpOperationDataCodes.SendObject: self.op_SendObject,
            # MtpOperationDataCodes.InitiateCapture: self.op_InitiateCapture,
            # MtpOperationDataCodes.FormatStore: self.op_FormatStore,
            # MtpOperationDataCodes.ResetDevice: self.op_ResetDevice,
            # MtpOperationDataCodes.SelfTest: self.op_SelfTest,
            # MtpOperationDataCodes.SetObjectProtection: self.op_SetObjectProtection,
            # MtpOperationDataCodes.PowerDown: self.op_PowerDown,
            # MtpOperationDataCodes.GetDevicePropDesc: self.op_GetDevicePropDesc,
            # MtpOperationDataCodes.GetDevicePropValue: self.op_GetDevicePropValue,
            # MtpOperationDataCodes.SetDevicePropValue: self.op_SetDevicePropValue,
            # MtpOperationDataCodes.ResetDevicePropValue: self.op_ResetDevicePropValue,
            # MtpOperationDataCodes.TerminateOpenCapture: self.op_TerminateOpenCapture,
            # MtpOperationDataCodes.MoveObject: self.op_MoveObject,
            # MtpOperationDataCodes.CopyObject: self.op_CopyObject,
            # MtpOperationDataCodes.GetPartialObject: self.op_GetPartialObject,
            # MtpOperationDataCodes.InitiateOpenCapture: self.op_InitiateOpenCapture,
            # MtpOperationDataCodes.GetObjectPropsSupported: self.op_GetObjectPropsSupported,
            # MtpOperationDataCodes.GetObjectPropDesc: self.op_GetObjectPropDesc,
            # MtpOperationDataCodes.GetObjectPropValue: self.op_GetObjectPropValue,
            # MtpOperationDataCodes.SetObjectPropValue: self.op_SetObjectPropValue,
            # MtpOperationDataCodes.GetObjectReferences: self.op_GetObjectReferences,
            # MtpOperationDataCodes.SetObjectReferences: self.op_SetObjectReferences,
            # MtpOperationDataCodes.Skip: self.op_Skip,
        }

    def handle_data(self, data):
        data, response = self._handle_data(data)
        if data is not None:
            if self.verbose > 0:
                print('[!] data: %s' % (hexlify(data)))
            self.resp_queue.insert(0, data)
        if response is not None:
            if self.verbose > 0:
                print('[!] response: %s' % (hexlify(response)))
            self.resp_queue.insert(0, response)

    def _handle_data(self, data):
        '''
        .. todo:: handle events ??
        '''
        print('[*] handling data. len: %#x' % len(data))
        if len(data) < 12:
            return mtp_error(None, MtpResponseCodes.INVALID_CODE_FORMAT)
        container = MtpContainer(data)
        if len(data) != container.length:
            return mtp_error(container, MtpResponseCodes.INVALID_CODE_FORMAT)
        if container.type == MtpContainerTypes.Command:
            if container.code in self.command_handlers:
                self.session_data['container_length'] = data[0:4]
                self.session_data['container_type'] = data[4:6]
                self.session_data['container_code'] = data[6:8]
                self.session_data['transaction_id'] = data[8:12]
                self.response_code = MtpResponseCodes.OK
                handler = self.command_handlers[container.code]
                result = handler(container)
                return (result, mtp_response(container, self.response_code))
        print('[!] unhandled code: %#x' % container.code)
        return mtp_error(container, MtpResponseCodes.OPERATION_NOT_SUPPORTED)

    def get_data(self):
        if self.resp_queue:
            return self.resp_queue.pop()

    @mutable('mtp_op_GetDeviceInfo_response')
    def op_GetDeviceInfo(self, container):
        # should parse this as well, but it will do for now...
        dev_info = unhexlify(
            '6400060000006400266d006900630072006f0073006f00660074002e006300' +
            '6f006d003a00200031002e0030003b00200061006e00640072006f00690064' +
            '002e0063006f006d003a00200031002e0030003b00000000001e0000000110' +
            '021003100410051006100710081009100a100b100c100d1014101510161017' +
            '101b100198029803980498059810981198c195c295c395c495c59506000000' +
            '0240034004400540064001c80400000001d402d403500150000000001a0000' +
            '000030013004300530083009300b30013802380438073808380b380d3801b9' +
            '02b903b982b983b984b905ba10ba11ba14ba82ba06b908730061006d007300' +
            '75006e006700000009470054002d004900390033003000300000000431002e' +
            '00300000001133003200330030006400300064003100630032003500330037' +
            '003000310031000000'
        )
        return mtp_data(container, dev_info)

    @mutable('mtp_op_OpenSession_response')
    def op_OpenSession(self, container):
        if container.length != 0x10:
            self.response_code = MtpResponseCodes.INVALID_DATASET
            return None
        self.session_data['session_id'] = container.data
        return None

    @mutable('mtp_op_CloseSession_response')
    def op_CloseSession(self, container):
        return None

    @mutable('mtp_op_GetStorageIDs_response')
    def op_GetStorageIDs(self, container):
        sids = b''
        for sid in self.storages:
            sids += MU32(sid)
        return mtp_data(container, sids)

    @mutable('mtp_op_GetStorageInfo_response')
    def op_GetStorageInfo(self, container):
        if container.length != 0x10:
            self.response_code = MtpResponseCodes.PARAMETER_NOT_SUPPORTED
            return None
        sid = struct.unpack('<I', container.data)[0]
        if sid not in self.storages:
            self.response_code = MtpResponseCodes.INVALID_STORAGE_ID
            return None
        storage_info = self.storages[sid].serialize()
        return mtp_data(container, storage_info)

    @mutable('mtp_op_GetNumObjects_response')
    def op_GetNumObjects(self, container):
        return None

    @mutable('mtp_op_GetObjectHandles_response')
    def op_GetObjectHandles(self, container):
        return None

    @mutable('mtp_op_GetObjectInfo_response')
    def op_GetObjectInfo(self, container):
        return None

    @mutable('mtp_op_GetObject_response')
    def op_GetObject(self, container):
        return None

    @mutable('mtp_op_GetThumb_response')
    def op_GetThumb(self, container):
        return None

    @mutable('mtp_op_DeleteObject_response')
    def op_DeleteObject(self, container):
        return None

    @mutable('mtp_op_SendObjectInfo_response')
    def op_SendObjectInfo(self, container):
        return None

    @mutable('mtp_op_SendObject_response')
    def op_SendObject(self, container):
        return None

    @mutable('mtp_op_InitiateCapture_response')
    def op_InitiateCapture(self, container):
        return None

    @mutable('mtp_op_FormatStore_response')
    def op_FormatStore(self, container):
        return None

    @mutable('mtp_op_ResetDevice_response')
    def op_ResetDevice(self, container):
        return None

    @mutable('mtp_op_SelfTest_response')
    def op_SelfTest(self, container):
        return None

    @mutable('mtp_op_SetObjectProtection_response')
    def op_SetObjectProtection(self, container):
        return None

    @mutable('mtp_op_PowerDown_response')
    def op_PowerDown(self, container):
        return None

    @mutable('mtp_op_GetDevicePropDesc_response')
    def op_GetDevicePropDesc(self, container):
        return None

    @mutable('mtp_op_GetDevicePropValue_response')
    def op_GetDevicePropValue(self, container):
        return None

    @mutable('mtp_op_SetDevicePropValue_response')
    def op_SetDevicePropValue(self, container):
        return None

    @mutable('mtp_op_ResetDevicePropValue_response')
    def op_ResetDevicePropValue(self, container):
        return None

    @mutable('mtp_op_TerminateOpenCapture_response')
    def op_TerminateOpenCapture(self, container):
        return None

    @mutable('mtp_op_MoveObject_response')
    def op_MoveObject(self, container):
        return None

    @mutable('mtp_op_CopyObject_response')
    def op_CopyObject(self, container):
        return None

    @mutable('mtp_op_GetPartialObject_response')
    def op_GetPartialObject(self, container):
        return None

    @mutable('mtp_op_InitiateOpenCapture_response')
    def op_InitiateOpenCapture(self, container):
        return None

    @mutable('mtp_op_GetObjectPropsSupported_response')
    def op_GetObjectPropsSupported(self, container):
        return None

    @mutable('mtp_op_GetObjectPropDesc_response')
    def op_GetObjectPropDesc(self, container):
        return None

    @mutable('mtp_op_GetObjectPropValue_response')
    def op_GetObjectPropValue(self, container):
        return None

    @mutable('mtp_op_SetObjectPropValue_response')
    def op_SetObjectPropValue(self, container):
        return None

    @mutable('mtp_op_GetObjectReferences_response')
    def op_GetObjectReferences(self, container):
        return None

    @mutable('mtp_op_SetObjectReferences_response')
    def op_SetObjectReferences(self, container):
        return None

    @mutable('mtp_op_Skip_response')
    def op_Skip(self, container):
        return None

    def get_mutation(self, stage, data=None):
        '''
        :param stage: stage name
        :param data: dictionary (string: bytearray) of data for the fuzzer (default: None)
        :return: mutation for current stage, None if not current fuzzing stage
        '''
        return self.app.get_mutation(stage, data)

    def get_session_data(self, stage):
        '''
        If an entity wants to pass specific data to the fuzzer when getting a mutation,
        it could return a session data here.
        This session data should be a dictionary of string:bytearray.
        The keys of the dictionary should match the keys in the templates.

        :param stage: stage that the session data is for
        :return: dictionary of session data
        '''
        return self.session_data


class USBMtpInterface(USBInterface):
    name = "USB MTP interface"

    def __init__(self, app, verbose=0):
        descriptors = {}
        self.mtp_device = MtpDevice(app, verbose)

        endpoints = [
            USBEndpoint(
                app=app,
                number=1,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=512,
                interval=0,
                handler=self.handle_ep1_data_available
            ),
            USBEndpoint(
                app=app,
                number=2,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=512,
                interval=0,
                handler=self.handle_ep2_buffer_available
            ),
            USBEndpoint(
                app=app,
                number=3,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_interrupt,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=512,
                interval=32,
                handler=self.handle_ep3_buffer_available
            ),
        ]

        # TODO: un-hardcode string index (last arg before "verbose")
        super(USBMtpInterface, self).__init__(
            app=app,
            interface_number=0,
            interface_alternate=0,
            interface_class=0xff,
            interface_subclass=0xff,
            interface_protocol=0,
            interface_string_index=0,
            verbose=verbose,
            endpoints=endpoints,
            descriptors=descriptors
        )

        # self.device_class = USBMtpClass(app, verbose)
        # self.device_class.set_interface(self)
        # OS String descriptor
        self.add_string_with_id(0xee, 'MSFT100'.encode('utf-16') + b'\x00\x00')

    def handle_ep1_data_available(self, data):
        if self.verbose > 0:
            print('in handle_ep1_data_available')
        self.mtp_device.handle_data(data)

    def handle_ep2_buffer_available(self):
        resp = self.mtp_device.get_data()
        if resp:
            print('[*] handle_ep2_buffer_available')
            self.app.send_on_endpoint(2, resp)

    def handle_ep3_buffer_available(self):
        # if self.verbose > 0:
        #     print('in handle_ep3_buffer_available')
        pass


class USBMsosVendor(USBVendor):

    def setup_request_handlers(self):
        self.local_handlers = {
            0x00: self.handle_msos_vendor_extended_config_descriptor,
        }
        self.request_handlers = {
            x: self.handle_all for x in self.local_handlers
        }

    def handle_all(self, req):
        handler = self.local_handlers[req.request]
        response = handler(req)
        if response is not None:
            self.app.send_on_endpoint(0, response)
        # self.supported()

    @mutable('msos_vendor_extended_config_descriptor')
    def handle_msos_vendor_extended_config_descriptor(self, req):
        '''
        Taken from OS_Desc_CompatID
        https://msdn.microsoft.com/en-us/windows/hardware/gg463179
        '''
        def pad(data, pad_len=8):
            to_pad = pad_len - len(data)
            return data + (b'\x00' * to_pad)

        self.property_sections = [
            [0x00, 0x01, pad(b'MTP'), pad(b''), pad(b'', 6)]
        ]
        bcdVersion = 0x0100
        wIndex = 0x00
        bCount = len(self.property_sections)
        reserved = pad(b'\x00', 7)
        properties = b''
        for prop in self.property_sections:
            properties += struct.pack('BB', prop[0], prop[1]) + prop[2] + prop[3] + prop[4]
        payload = struct.pack('<HHB', bcdVersion, wIndex, bCount) + reserved + properties
        dwLength = len(payload) + 4
        payload = struct.pack('<I', dwLength) + payload
        return payload


class USBMtpDevice(USBDevice):
    name = "USB MTP device"

    def __init__(self, app, vid, pid, rev, verbose=0, **kwargs):
        interface = USBMtpInterface(app, verbose=verbose)
        config = USBConfiguration(
            app=app,
            configuration_index=1,
            configuration_string="Android MTP Device",
            interfaces=[interface]
        )
        super(USBMtpDevice, self).__init__(
            app=app,
            device_class=0,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=vid,
            product_id=pid,
            device_rev=rev,
            manufacturer_string="Samsung Electronics Co., Ltd",
            product_string="GT-I9250 Phone [Galaxy Nexus](Mass storage mode)",
            serial_number_string="00001",
            configurations=[config],
            descriptors={},
            verbose=verbose
        )
        self.device_vendor = USBMsosVendor(app=app, verbose=verbose)
        self.device_vendor.set_device(self)
