from threading import Thread
from socket import *
import sys
import traceback


class netserver(Thread):
    def __init__(self, app, port):
        super(netserver, self).__init__()
        self.app = app
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.app.netserver_to_endpoint_sd = self.sock
        self.app.netserver_sd = self.sock
        try:
            self.sock.bind(('', port))
        except:
            print("Error: Could not bind to local port")
            return

        self.sock.listen(5)

    def run(self):
        newsock = 0
        while self.app.server_running:
            try:
                if not newsock:
                    newsock, address = self.sock.accept()
                self.app.netserver_from_endpoint_sd = newsock
                reply = newsock.recv(16384)
                if len(reply) > 0:
                    print ("Socket reply: %s" % reply)
                    self.app.reply_buffer = reply
            except:
                print("Error: Socket Accept")
                print(traceback.format_exc())
                sys.exit()

        self.app.netserver_to_endpoint_sd.close()
        self.app.netserver_from_endpoint_sd.close()
