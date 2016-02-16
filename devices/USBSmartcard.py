# USBSmartcard.py
#
# Contains class definitions to implement a USB Smartcard.

# This devbice doesn't work properly yet!!!!!

from USB import *
from USBDevice import *
from USBConfiguration import *
from USBInterface import *
from USBEndpoint import *


class USBSmartcardClass(USBClass):
    name = "USB Smartcard class"

    def setup_request_handlers(self):
        self.request_handlers = {
            0x02: self.handle_get_clock_frequencies
        }

    def handle_get_clock_frequencies(self, req):
        response = b'\x67\x32\x00\x00\xCE\x64\x00\x00\x9D\xC9\x00\x00\x3A\x93\x01\x00\x74\x26\x03\x00\xE7\x4C\x06\x00\xCE\x99\x0C\x00\xD7\x5C\x02\x00\x11\xF0\x03\x00\x34\x43\x00\x00\x69\x86\x00\x00\xD1\x0C\x01\x00\xA2\x19\x02\x00\x45\x33\x04\x00\x8A\x66\x08\x00\x0B\xA0\x02\x00\x73\x30\x00\x00\xE6\x60\x00\x00\xCC\xC1\x00\x00\x99\x83\x01\x00\x32\x07\x03\x00\x63\x0E\x06\x00\xB3\x22\x01\x00\x7F\xE4\x01\x00\x06\x50\x01\x00\x36\x97\x00\x00\x04\xFC\x00\x00\x53\x28\x00\x00\xA5\x50\x00\x00\x4A\xA1\x00\x00\x95\x42\x01\x00\x29\x85\x02\x00\xF8\x78\x00\x00\x3E\x49\x00\x00\x7C\x92\x00\x00\xF8\x24\x01\x00\xF0\x49\x02\x00\xE0\x93\x04\x00\xC0\x27\x09\x00\x74\xB7\x01\x00\x6C\xDC\x02\x00\xD4\x30\x00\x00\xA8\x61\x00\x00\x50\xC3\x00\x00\xA0\x86\x01\x00\x40\x0D\x03\x00\x80\x1A\x06\x00\x48\xE8\x01\x00\xBA\xDB\x00\x00\x36\x6E\x01\x00\x24\xF4\x00\x00\xDD\x6D\x00\x00\x1B\xB7\x00\x00'
        self.maxusb_app.send_on_endpoint(0, response)


class USBSmartcardInterface(USBInterface):
    name = "USB Smartcard interface"

    def __init__(self, maxusb_app, verbose=0):
        bLength = b'\x36'
        bDescriptorType = b'\x21'   # USB-ICC
        bcdCCID = b'\x10\x01'
        bMaxSlotIndex = b'\x00'  # index of highest available slot
        bVoltageSupport = b'\x07'
        dwProtocols = b'\x03\x00\x00\x00'
        dwDefaultClock = b'\xA6\x0E\x00\x00'
        dwMaximumClock = b'\x4C\x1D\x00\x00'
        bNumClockSupported = b'\x00'
        dwDataRate = b'\x60\x27\x00\x00'
        dwMaxDataRate = b'\xB4\xC4\x04\x00'
        bNumDataRatesSupported = b'\x00'
        dwMaxIFSD = b'\xFE\x00\x00\x00'
        dwSynchProtocols = b'\x00\x00\x00\x00'
        dwMechanical = b'\x00\x00\x00\x00'
        dwFeatures = b'\x30\x00\x01\x00'
        dwMaxCCIDMessageLength = b'\x0F\x01\x00\x00'
        bClassGetResponse = b'\x00'
        bClassEnvelope = b'\x00'
        wLcdLayout = b'\x00\x00'
        bPinSupport = b'\x00'
        bMaxCCIDBusySlots = b'\x01'

        self.icc_descriptor = (
            bLength +
            bDescriptorType +
            bcdCCID +
            bMaxSlotIndex +
            bVoltageSupport +
            dwProtocols +
            dwDefaultClock +
            dwMaximumClock +
            bNumClockSupported +
            dwDataRate +
            dwMaxDataRate +
            bNumDataRatesSupported +
            dwMaxIFSD +
            dwSynchProtocols +
            dwMechanical +
            dwFeatures +
            dwMaxCCIDMessageLength +
            bClassGetResponse +
            bClassEnvelope +
            wLcdLayout +
            bPinSupport +
            bMaxCCIDBusySlots
        )

        descriptors = {
            USB.desc_type_hid: self.icc_descriptor  # 33 is the same descriptor type code as HID
        }

        endpoints = [
            USBEndpoint(
                maxusb_app=maxusb_app,
                number=3,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_interrupt,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=16384,
                interval=8,
                handler=self.handle_buffer_available
            ),
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
                number=2,
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
        super(USBSmartcardInterface, self).__init__(
                maxusb_app=maxusb_app,
                interface_number=0,
                interface_alternate=0,
                interface_class=0x0b,
                interface_subclass=0,
                interface_protocol=0,
                interface_string_index=0,
                verbose=verbose,
                endpoints=endpoints,
                descriptors=descriptors
        )

        self.device_class = USBSmartcardClass(maxusb_app)
        self.trigger = False
        self.initial_data = b'\x50\x03'

    def handle_data_available(self, data):
        self.supported()
#        print ("Received:",data)
        command = ord(data[:1])
#        print ("command=%02x" % command)
        bSeq = data[6:7]
#        print ("seq=",ord(bSeq))
        bReserved = ord(data[7:8])
#        print ("bReserved=",bReserved) 

        if self.maxusb_app.server_running:
            try:
                self.maxusb_app.netserver_from_endpoint_sd.send(data)
            except:
                print ("Error: No network client connected")

            while True:
                if len(self.maxusb_app.reply_buffer) > 0:
                    self.maxusb_app.send_on_endpoint(2, self.maxusb_app.reply_buffer)
                    self.maxusb_app.reply_buffer = ""
                    break

        elif command == 0x61: # PC_to_RDR_SetParameters

            if self.maxusb_app.testcase[1] == "SetParameters_bMessageType":
                bMessageType = self.maxusb_app.testcase[2]
            else:
                bMessageType = b'\x82'  # RDR_to_PC_Parameters
            if self.maxusb_app.testcase[1] == "SetParameters_dwLength":
                dwLength = self.maxusb_app.testcase[2]
            else:
                dwLength = b'\x05\x00\x00\x00' # Message-specific data length
            if self.maxusb_app.testcase[1] == "SetParameters_bSlot":
                bSlot = self.maxusb_app.testcase[2]
            else:
                bSlot = b'\x00' # fixed for legacy reasons
            if self.maxusb_app.testcase[1] == "SetParameters_bStatus":
                bStatus = self.maxusb_app.testcase[2]
            else:
                bStatus = b'\x00' # reserved
            if self.maxusb_app.testcase[1] == "SetParameters_bError":
                bError = self.maxusb_app.testcase[2]
            else:
                bError = b'\x80'
            if self.maxusb_app.testcase[1] == "SetParameters_bProtocolNum":
                bProtocolNum = self.maxusb_app.testcase[2]
            else:
                bProtocolNum = b'\x00'

            abProtocolDataStructure = b'\x11\x00\x00\x0a\x00'
            
            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        bStatus + \
                        bError + \
                        bProtocolNum + \
                        abProtocolDataStructure      

 
        elif command == 0x62: # PC_to_RDR_IccPowerOn

            if bReserved == 2:

                if self.maxusb_app.testcase[1] == "IccPowerOn_bMessageType":
                    bMessageType = self.maxusb_app.testcase[2]
                else:
                    bMessageType = b'\x80'  # RDR_to_PC_DataBlock
                if self.maxusb_app.testcase[1] == "IccPowerOn_dwLength":
                    dwLength = self.maxusb_app.testcase[2]
                else:
                    dwLength = b'\x12\x00\x00\x00' # Message-specific data length
                if self.maxusb_app.testcase[1] == "IccPowerOn_bSlot":
                    bSlot = self.maxusb_app.testcase[2]
                else:
                    bSlot = b'\x00' # fixed for legacy reasons
                if self.maxusb_app.testcase[1] == "IccPowerOn_bStatus":
                    bStatus = self.maxusb_app.testcase[2]
                else:
                    bStatus = b'\x00'
                if self.maxusb_app.testcase[1] == "IccPowerOn_bError":
                    bError = self.maxusb_app.testcase[2]
                else:
                    bError = b'\x80'
                if self.maxusb_app.testcase[1] == "IccPowerOn_bChainParameter":
                    bChainParameter = self.maxusb_app.testcase[2]
                else:
                    bChainParameter = b'\x00'
                abData = b'\x3b\x6e\x00\x00\x80\x31\x80\x66\xb0\x84\x12\x01\x6e\x01\x83\x00\x90\x00'
                response =  bMessageType + \
                            dwLength + \
                            bSlot + \
                            bSeq + \
                            bStatus + \
                            bError + \
                            bChainParameter + \
                            abData

            else:
                if self.maxusb_app.testcase[1] == "IccPowerOn_bMessageType":
                    bMessageType = self.maxusb_app.testcase[2]
                else:
                    bMessageType = b'\x80'  # RDR_to_PC_DataBlock
                if self.maxusb_app.testcase[1] == "IccPowerOn_dwLength":
                    dwLength = self.maxusb_app.testcase[2]
                else:
                    dwLength = b'\x00\x00\x00\x00' # Message-specific data length
                if self.maxusb_app.testcase[1] == "IccPowerOn_bSlot":
                    bSlot = self.maxusb_app.testcase[2]
                else:
                    bSlot = b'\x00' # fixed for legacy reasons
                if self.maxusb_app.testcase[1] == "IccPowerOn_bStatus":
                    bStatus = self.maxusb_app.testcase[2]
                else:
                    bStatus = b'\x40'
                if self.maxusb_app.testcase[1] == "IccPowerOn_bError":
                    bError = self.maxusb_app.testcase[2]
                else:
                    bError = b'\xfe'
                if self.maxusb_app.testcase[1] == "IccPowerOn_bChainParameter":
                    bChainParameter = self.maxusb_app.testcase[2]
                else:
                    bChainParameter = b'\x00'

                response =  bMessageType + \
                            dwLength + \
                            bSlot + \
                            bSeq + \
                            bStatus + \
                            bError + \
                            bChainParameter



        elif command == 0x63: # PC_to_RDR_IccPowerOff

            if self.maxusb_app.testcase[1] == "IccPowerOff_bMessageType":
                bMessageType = self.maxusb_app.testcase[2]
            else:
                bMessageType = b'\x81'  # PC_to_RDR_IccPowerOff
            if self.maxusb_app.testcase[1] == "IccPowerOff_dwLength":
                dwLength = self.maxusb_app.testcase[2]
            else:
                dwLength = b'\x00\x00\x00\x00' # Message-specific data length
            if self.maxusb_app.testcase[1] == "IccPowerOff_bSlot":
                bSlot = self.maxusb_app.testcase[2]
            else:
                bSlot = b'\x00' # fixed for legacy reasons
            if self.maxusb_app.testcase[1] == "IccPowerOff_abRFU":
                abRFU = self.maxusb_app.testcase[2]            
            else:
                abRFU = b'\x01' # reserved

            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        abRFU


        elif command == 0x65: # PC_to_RDR_GetSlotStatus


            bMessageType = b'\x81'  # RDR_to_PC_SlotStatus
            dwLength = b'\x00\x00\x00\x00' # Message-specific data length
            bSlot = b'\x00'
            bStatus = b'\x01'
            bError = b'\x00'
            bClockStatus = b'\x00' # reserved

            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        bStatus + \
                        bError + \
                        bClockStatus




                    

        elif command == 0x6b: # PC_to_RDR_Escape

           
            bMessageType = b'\x83'  # RDR_to_PC_Escape
            dwLength = b'\x00\x00\x00\x00' # Message-specific data length
            bSlot = b'\x00'
            bStatus = b'\x41'
            bError = b'\x0a'
            bRFU = b'\x00' # reserved

            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        bStatus + \
                        bError + \
                        bRFU


        elif command == 0x6f: # PC_to_RDR_XfrBlock message

            if self.maxusb_app.testcase[1] == "XfrBlock_bMessageType":
                bMessageType = self.maxusb_app.testcase[2]
            else:
                bMessageType = b'\x80'  # RDR_to_PC_DataBlock
            if self.maxusb_app.testcase[1] == "XfrBlock_dwLength":
                dwLength = self.maxusb_app.testcase[2]
            else:
                dwLength = b'\x02\x00\x00\x00' # Message-specific data length
            if self.maxusb_app.testcase[1] == "XfrBlock_bSlot":
                bSlot = self.maxusb_app.testcase[2]
            else:
                bSlot = b'\x00' # fixed for legacy reasons
            if self.maxusb_app.testcase[1] == "XfrBlock_bStatus":
                bStatus = self.maxusb_app.testcase[2]
            else:
                bStatus = b'\x00' # reserved
            if self.maxusb_app.testcase[1] == "XfrBlock_bError":
                bError = self.maxusb_app.testcase[2]
            else:
                bError = b'\x80'
            if self.maxusb_app.testcase[1] == "XfrBlock_bChainParameter":
                bChainParameter = self.maxusb_app.testcase[2]
            else:
                bChainParameter = b'\x00'
            abData = b'\x6a\x82' 

            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        bStatus + \
                        bError + \
                        bChainParameter + \
                        abData

        elif command == 0x73: # PC_to_RDR_SetDataRateAndClockFrequency

            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_bMessageType":
                bMessageType = self.maxusb_app.testcase[2]
            else:
                bMessageType = b'\x84'  # RDR_to_PC_DataRateAndClockFrequency
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_dwLength":
                dwLength = self.maxusb_app.testcase[2]
            else:
                dwLength = b'\x08\x00\x00\x00' # Message-specific data length
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_bSlot":
                bSlot = self.maxusb_app.testcase[2]
            else:
                bSlot = b'\x00' # fixed for legacy reasons
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_bStatus":
                bStatus = self.maxusb_app.testcase[2]
            else:
                bStatus = b'\x00' # reserved
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_bError":
                bError = self.maxusb_app.testcase[2]
            else:
                bError = b'\x80'
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_bRFU":
                bRFU = self.maxusb_app.testcase[2]
            else:
                bRFU = b'\x80'
            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_dwClockFrequency":
                dwClockFrequency = self.maxusb_app.testcase[2]
            else:
                dwClockFrequency = b'\xA6\x0E\x00\x00'

            if self.maxusb_app.testcase[1] == "SetDataRateAndClockFrequency_dwDataRate":
                dwDataRate = self.maxusb_app.testcase[2]
            else:
                dwDataRate = b'\x60\x27\x00\x00' 

            response =  bMessageType + \
                        dwLength + \
                        bSlot + \
                        bSeq + \
                        bStatus + \
                        bError + \
                        bRFU + \
                        dwClockFrequency + \
                        dwDataRate

        else:
            print ("Received Smartcard command not understood") 
            response = b''

        if not self.maxusb_app.server_running:
            self.configuration.device.maxusb_app.send_on_endpoint(2, response)

    def handle_buffer_available(self):
        if not self.trigger:
            self.configuration.device.maxusb_app.send_on_endpoint(3, self.initial_data)
            self.trigger = True


class USBSmartcardDevice(USBDevice):
    name = "USB Smartcard device"

    def __init__(self, maxusb_app, vid, pid, rev, verbose=0, **kwargs):
        interface = USBSmartcardInterface(maxusb_app, verbose=verbose)

        config = USBConfiguration(
                maxusb_app=maxusb_app,
                configuration_index=1,
                configuration_string="Emulated Smartcard",
                interfaces=[interface]
        )

        super(USBSmartcardDevice, self).__init__(
            maxusb_app=maxusb_app,
            device_class=0,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=vid,
            product_id=pid,
            device_rev=rev,
            manufacturer_string="Generic",
            product_string="Smart Card Reader Interface",
            serial_number_string="20070818000000000",
            configurations=[config],
            verbose=verbose
        )
