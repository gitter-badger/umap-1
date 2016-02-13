#!/usr/bin/env python3
'''
Umap & Kitty integration
This script initializes and runs the USB device stack

Usage:
    umap_stack.py fuzz --port SERIAL_PORT --device DEVICE_CLASS [--fuzzer-host HOST] [--fuzzer-port PORT] [--verbose ...]
    umap_stack.py list classes
    umap_stack.py list subclasses <CLASS>

Options:
    -P --port SERIAL_PORT       facedancer's serial port
    -D --device DEVICE_CLASS    class of the deivce
    -h --fuzzer-host HOST       hostname or IP of the fuzzer [defualt: '127.0.0.1']
    -p --fuzzer-port PORT       port of the fuzzer [default: 26010]
    -v --verbose                verbosity level
'''
import docopt
import traceback
import time
from kitty.remote.rpc import RpcClient
from Facedancer import Facedancer
from MAXUSBApp import MAXUSBApp
from serial import Serial, PARITY_NONE

from devices.USBKeyboard import USBKeyboardDevice
from devices.USBAudio import USBAudioDevice
from devices.USBCDC import USBCDCDevice

list_cmd = 'umap_stack.py list classes'

class_map = {
    'keyboard': {
        'fd_class': USBKeyboardDevice,
        'classes': [3],
        'params': {
            'vid': 0x413c,
            'pid': 0x2107,
            'rev': 0x0178,
        },
    },
    'audio': {
        'fd_class': USBAudioDevice,
        'classes': [1],
        'params': {
            'vid': 0x041e,
            'pid': 0x0402,
            'rev': 0x0100,
        }
    },
    'CDC': {
        'fd_class': USBCDCDevice,
        'classes': [2, 10],
        'params': {
            'vid': 0x2548,
            'pid': 0x1001,
            'rev': 0x1000,
        }
    }
}

default_params = {
    'vid': 0x1111,
    'pid': 0x2222,
    'rev': 0x3333,
    'subclass': 0,
    'proto': 0,
}


def build_fuzzer(options):
    return None
    fuzzer = RpcClient(host=options['--fuzzer-host'], port=int(options['--fuzzer-port']))
    return fuzzer


def build_device(fuzzer, options):
    sp = Serial(options['--port'], 115200, parity=PARITY_NONE, timeout=2)
    verbosity = options['--verbose']
    logfp = None
    mode = 2
    current_testcase = None
    fd = Facedancer(sp, verbose=verbosity)
    app = MAXUSBApp(fd, logfp, mode, current_testcase, verbose=verbosity, fuzzer=fuzzer)
    dev_class = options['--device']
    if dev_class not in class_map:
        raise Exception('Unknown device: %s, run `%s` to list supported devices' % (dev_class, list_cmd))
    device_config = class_map[dev_class]
    params = default_params.copy()
    params.update(device_config['params'])
    params['verbose'] = verbosity
    device = device_config['fd_class'](app, **params)
    return device


def run_device(device, options):
    try:
        device.connect()
        device.run()
    except:
        print('Got exception while connecting/running device')
        print(traceback.format_exc())
    device.disconnect()


def kmap_fuzz(options):
    fuzzer = build_fuzzer(options)
    umap = build_device(fuzzer, options)
    run_device(umap, options)


def kmap_list(options):
    if options['classes']:
        for cls in class_map:
            print(cls)
            # print('%-20s%s' % (cls, ', '.join('%02x' % v for v in class_map[cls]['values'])))
    elif options['subclasses']:
        cls = options['<CLASS>']
        if cls not in class_map:
            raise Exception('Unkown class specified. run `%s` to see list of available classes' % (list_cmd))
        if 'subclasses' in class_map[cls]:
            for subclass in class_map[cls]['subclasses']:
                print(subclass)


def main():
    options = docopt.docopt(__doc__)
    print(options)
    if options['list']:
        kmap_list(options)
    elif options['fuzz']:
        kmap_fuzz(options)


if __name__ == '__main__':
    main()
