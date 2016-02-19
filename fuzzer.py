#!/usr/bin/env python
'''
Kitty fuzzer that should work with the umap_stack.py
'''
import sys
from kitty.remote.rpc import RpcServer
from kitty.fuzzers import ClientFuzzer
from kitty.targets import ClientTarget
from kitty.interfaces import WebInterface
from kitty.model import GraphModel

import os
import time
from kitty.controllers import ClientController
from katnip.templates.usb import device_descriptor


class UmapController(ClientController):
    '''
    Trigger a USB reconnection -
    Signal the Umap to disconnect / reconnect using files.
    '''

    def __init__(self):
        super(UmapController, self).__init__('UmapController')
        self.trigger_dir = '/tmp/umap_kitty'
        self.reconnect_file = 'trigger_reconnect'

    def del_file(self, filename):
        path = os.path.join(self.trigger_dir, filename)
        if os.path.isfile(path):
            os.remove(path)

    def cleanup_triggers(self):
        if not os.path.isdir(self.trigger_dir):
            if not os.path.exists(self.trigger_dir):
                os.mkdir(self.trigger_dir)
        self.del_file(self.reconnect_file)

    def setup(self):
        super(UmapController, self).setup()
        self.cleanup_triggers()

    def trigger(self):
        self.logger.info('trigger reconnection')
        self.do(self.reconnect_file)

    def do(self, filename):
        count = 0
        path = os.path.join(self.trigger_dir, filename)
        open(path, 'a').close()
        while os.path.isfile(path):
            time.sleep(0.01)
            if count % 1000 == 0:
                self.logger.warning('still waiting for umap_stack to remove the file %s' % path)
            count += 1


def get_model():
    model = GraphModel()
    model.connect(device_descriptor)
    return model


def main():
    fuzzer = ClientFuzzer(name='UmapFuzzer', option_line=' '.join(sys.argv[1:]))

    fuzzer.set_interface(WebInterface())

    target = ClientTarget(name='USBTarget')
    target.set_controller(UmapController())
    target.set_mutation_server_timeout(3)

    model = get_model()
    fuzzer.set_model(model)
    fuzzer.set_target(target)

    remote = RpcServer(host='localhost', port=26007, impl=fuzzer)
    remote.start()


if __name__ == '__main__':
    main()
