# -*- coding: utf-8 -*-
"""
@author: Robert Rehammar

A VISA Raw server.

Copyright (c) 2016 Qamcom Research and Technology

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import socket
import sys, getopt
from threading import Thread
import select
from time import sleep
from visa_socket import Visasocket

class Queue:
    def __init__(self):
        self.items = []

    def __str__(self):
        return self.items.__str__()
    
    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

class Visaserver:
    """
    A VISA server for raw socket connections.

    Does bind and listen automatically
    """
    def __init__(self, sock=None, host = '', idn = "Undefined", port = 9876, no_conns = 5):
        """
        @param Sock socket to use. If None, a new will be created.
        @param Host set what to bind to, default bind to all.
        @param idn Selected *IDN? response
        @param settings If None, try to read all setting from the filename in settings. Not supported
        @param port The port to use, default is 9876.
        @param no_conns Maximum number of connections.
        """
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

        self._port = port
        self._host = host
        # General VISA settings:
        self._idn = idn

        # Dictionary holding all functions that should be run for a given command:
        # structure is: [default callback function, error callback function]
        self._callbacks = dict()
        self.set_callback('*idn?', self.idn, self.idn_error, [])

        self.bind(self._host, self._port)
        self.listen(no_conns)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("running __exit__")
#        self._clientsocket.close()
        self.sock.close()

    def idn(self, params, extra_params):
        return self._idn

    def idn_error(self):
        return self._idn
#        return "*IDN? expects no parameter"

    def run(self):
        """
        Main run function to run the server.
        """
        print("running run()")
        with self.accept() as self._clientsocket:
            cmds = Queue()
            old_partial_cmd = ''
            while True:
                msg = self._clientsocket.receive()
                if msg == '':
                    # This means the connection was closed, and the server should exit.
                    break
                # Extract command and parameter(s):
                # FIXME: move this stuff to the server receive function.
                # FIXME: first join with old cmd and then split on \n and then take the last cmd
                msg = old_partial_cmd + msg
                print(msg)
                res = msg.split('\n')
                print(res)
                old_partial_cmd = res.pop() # Store any partial command for later
                print(old_partial_cmd)
                for cmd in res:
                    cmds.enqueue(cmd)
                print(cmds)
                if not cmds.size():
                    continue
                else:
                    msg = cmds.dequeue()
                    res = msg.split(' ')#cmd, param = msg.split(' ')
                    cmd = res[0]
                    cmd = cmd.upper()#.replace('\n','')
                    print("Got "+cmd)
                    if len(res) > 1:
                        params = res[1:]
                    else:
                        params = list()
                    result = list()
                    try:
                        print(cmd)
                        extra_params = self._callbacks[cmd][2]
                        result = self._callbacks[cmd][0](params, extra_params)
                    except KeyError as e:
                        print("visaserver: Got unknown command", e)
                    else:
                        if result:
                            self._clientsocket.send(result)
                    # FIXME: handle network errors some how...?
                    sleep(0.1)

    def set_callback(self, command, callback, error_callback, extra_params = []):
        """
    	set callback function for the different SCPI commands.
    	@param command The SCPI command
    	@param callback The default callback
    	@param error_callback Callback to call if there was an error WHEN??
    	@param extra_params List of extra parameters to geve to the callback and error_callback functions.
    	"""
        # FIXME: instead of a list it would be better to have callback-objects of some class.
        print("Generating callback for command '%s' with list:\n"%command, [callback, error_callback, extra_params])
        self._callbacks[command.upper()] = [callback, error_callback, extra_params]

    def bind(self, host, port):
        self.sock.bind((host, port)) # or socket.gethostname() or '' for all interfaces
    
    def listen(self, no_connections = 5):
        return self.sock.listen(no_connections)
    
    def accept(self):
        conn, address = self.sock.accept()
        return Visasocket(conn)#, address
        
    def setblocking(self, value):
        return self.sock.setblocking(value)

def main(argv):
    pass

if __name__ == "__main__":
    main(argv[1:])
