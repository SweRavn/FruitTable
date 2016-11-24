# -*- coding: utf-8 -*-
"""
@author: Robert Rehammar

Class to communicate the VISA/RawSocket TCP/IP protocol using the
TCPIP::address::port::SOCKET VISA designator.

Requires: python 3.

Copyright (c) 2016 Qamcom Research and Technology

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import select
import time

class Visasocket:
    def __init__(self, sock=None):
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Running xvisocket exit")
        try:
            self.sock.close()
        except:
            pass

    def connect(self, host, port):
        self.sock.connect((host, port))

    def setblocking(self, value):
        return self.sock.setblocking(value)
    
    def settimeout(self, timeout):
        return self.sock.settimeout(timeout)

    def send(self, msg):
        print("Running send with '"+msg+"'")
#        totalsent = 0
#        while totalsent < len(msg):
#            print(totalsent)
#            sent = self.sock.send(msg[totalsent:].encode())
        res = self.sock.sendall(msg.encode())
        if res:
#            if sent == 0:
            raise RuntimeError("socket connection broken")
#            totalsent = totalsent + sent
#        return totalsent
        return res
    
#    def receive(self):
#        print('Running receive')
#        chunks = list()
#        bytes_recd = 0
##        ready = select.select([self.sock], [], [], 1) # Timeout is 1 s, see http://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
##        if not ready[0]:
##            raise socket.timeout
##        else:
#        chunk = ''
#        while chunk != '\n':
#            chunk = self.sock.recv(1).decode("utf-8") 
#            bytes_recd = bytes_recd + len(chunk)
#            chunks.append(chunk)
#        print(chunks)
#        return ''.join(chunks)


    def receive(self):
        print('Running receive')
#        print(self.sock.
#        print(time.localtime())
        ready = select.select([self.sock], [], [])
#        print(time.localtime())
#        print(ready)
        chunk = self.sock.recv(4096).decode("utf-8") 
        return chunk
